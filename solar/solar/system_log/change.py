#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import dictdiffer
import networkx as nx

from solar.core.log import log
from solar.core import signals
from solar.core import resource
from solar import utils
from solar.interfaces.db import get_db
from solar.system_log import data
from solar.orchestration import graph
from solar.events import api as evapi
from solar.interfaces import orm

db = get_db()


def guess_action(from_, to):
    # NOTE(dshulyak) imo the way to solve this - is dsl for orchestration,
    # something where this action will be excplicitly specified
    if not from_:
        return 'run'
    elif not to:
        return 'remove'
    else:
        return 'update'


def create_diff(staged, commited):
    return list(dictdiffer.diff(commited, staged))


def create_logitem(resource, action, diffed, connections_diffed):
    return data.LogItem(
                utils.generate_uuid(),
                resource,
                '{}.{}'.format(resource, action),
                diffed,
                connections_diffed)


def create_sorted_diff(staged, commited):
    staged.sort()
    commited.sort()
    return create_diff(staged, commited)


def stage_changes():
    log = data.SL()
    log.clean()
    resources_map = {r.name: r for r in resource.load_all()}
    commited_map = {r.id for r in orm.DBCommitedState.load_all()}

    for resource_id in set(resources_map.keys()) | set(commited_map.keys()):

        if resource_id not in resource_map:
            resource_args = {}
            resource_connections = []
        else:
            resource_args = resource_map[resource_id].args
            resource_connections = resource_map[resource_id].connections

        if resource_id not in commited_map:
            commited_args = {}
            commited_connections = []
        else:
            commited_args = commited_map[resource_id].inputs
            commited_connections = commited_map[resource_id].connections

        inputs_diff = create_diff(resource_args, commited_args)
        connections_diff = create_sorted_diff(
            resource_connections, commited_connections)

        # if new connection created it will be reflected in inputs
        # but using inputs to reverse connections is not possible
        if inputs_diff:
            log_item = create_logitem(
                resource_id,
                guess_action(commited_connections, resource_connections),
                inputs_diff,
                connections_diff,
                base_path=resource_obj.base_path)
            log.append(log_item)
    return log


def send_to_orchestration():
    dg = nx.MultiDiGraph()

    events = {}
    changed_nodes = []

    for resource_obj in resource.load_all():
        commited_db_obj = resource_obj.load_commited()
        resource_args = resource_obj.args

        df = create_diff(resource_args, commited_db_obj.inputs)

        if df:
            events[resource_obj.name] = evapi.all_events(resource_obj.name)
            changed_nodes.append(resource_obj.name)
            action = guess_action(resource_args, commited_db_obj.inputs)

            state_change = evapi.StateChange(resource_obj.name, action)
            state_change.insert(changed_nodes, dg)

    evapi.build_edges(dg, events)

    # what it should be?
    dg.graph['name'] = 'system_log'
    return graph.create_plan_from_graph(dg)


def parameters(res, action, data):
    return {'args': [res, action],
            'type': 'solar_resource',
            # unique identifier for a node should be passed
            'target': data.get('ip')}


def revert_uids(uids):
    history = data.CL()
    for uid in uids:
        item = history.get(uid)
        res_db = resource.load(item.res)
        commited = res_db.load_commited()
        args_to_update = dictdiffer.revert(
            item.diff, commited.inputs)
        res_db.update(args_to_update)


def revert(uid):
    return revert_uids([uid])

