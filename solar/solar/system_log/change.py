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
from .consts import CHANGES

db = get_db()


def guess_action(from_, to):
    # NOTE(dshulyak) imo the way to solve this - is dsl for orchestration,
    # something where this action will be excplicitly specified
    if not from_:
        return CHANGES.run.name
    elif not to:
        return CHANGES.remove.name
    else:
        return CHANGES.update.name


def create_diff(staged, commited):
    return list(dictdiffer.diff(commited, staged))


def create_logitem(resource, action, diffed, connections_diffed,
                   base_path=None):
    return data.LogItem(
                utils.generate_uuid(),
                resource,
                action,
                diffed,
                connections_diffed,
                base_path=base_path)


def create_sorted_diff(staged, commited):
    staged.sort()
    commited.sort()
    return create_diff(staged, commited)



def stage_changes():
    log = data.SL()
    log.clean()
    resources_map = {r.name: r for r in resource.load_all()}
    commited_map = {r.id: r for r in orm.DBCommitedState.load_all()}

    for resource_id in set(resources_map.keys()) | set(commited_map.keys()):

        if resource_id not in resources_map:
            resource_args = {}
            resource_connections = []
            base_path = commited_map[resource_id].base_path
        else:
            resource_args = resources_map[resource_id].args
            resource_connections = resources_map[resource_id].connections
            base_path = resources_map[resource_id].base_path

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
                guess_action(commited_args, resource_args),
                inputs_diff,
                connections_diff,
                base_path=base_path)
            log.append(log_item)
    return log


def send_to_orchestration():
    dg = nx.MultiDiGraph()
    events = {}
    changed_nodes = []

    for logitem in data.SL():
        events[logitem.res] = evapi.all_events(logitem.res)
        changed_nodes.append(logitem.res)

        state_change = evapi.StateChange(logitem.res, logitem.action)
        state_change.insert(changed_nodes, dg)

    evapi.build_edges(dg, events)

    # what `name` should be?
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
        if item.action == CHANGES.update.name:
            _revert_update(item)
        elif item.action == CHANGES.remove.name:
            _revert_remove(item)
        elif item.action == CHANGES.run.name:
            _revert_run(item)
        else:
            log.debug('Action %s for resource %s is a side'
                      ' effect of another action', item.action, item.res)


def _revert_remove(logitem):
    """Resource should be created with all previous connections
    """
    commited = orm.DBCommitedState.load(logitem.res)
    args = dictdiffer.revert(logitem.diff, commited.inputs)
    connections = dictdiffer.revert(logitem.signals_diff, sorted(commited.connections))
    resource.Resource(logitem.res, logitem.base_path, args=args)
    for emitter, emitter_input, receiver, receiver_input in connections:
        emmiter_obj = resource.load(emitter)
        receiver_obj = resource.load(receiver)
        signals.connect(emmiter_obj, receiver_obj, {emitter_input: receiver_input})


def _revert_update(logitem):
    """Revert of update should update inputs and connections
    """
    res_obj = resource.load(logitem.res)
    commited = res_obj.load_commited()
    args_to_update = dictdiffer.revert(logitem.diff, commited.inputs)
    res_obj.update(args_to_update)

    for emitter, _, receiver, _ in commited.connections:
        emmiter_obj = resource.load(emitter)
        receiver_obj = resource.load(receiver)
        signals.disconnect(emmiter_obj, receiver_obj)

    connections = dictdiffer.revert(logitem.signals_diff, sorted(commited.connections))
    for emitter, emitter_input, receiver, receiver_input in connections:
        emmiter_obj = resource.load(emitter)
        receiver_obj = resource.load(receiver)
        signals.connect(emmiter_obj, receiver_obj, {emitter_input: receiver_input})


def _revert_run(logitem):
    res_obj = resource.load(logitem.res)
    res_obj.delete()


def revert(uid):
    return revert_uids([uid])

