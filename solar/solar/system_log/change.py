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


def create_logitem(resource, action, diffed):
    return data.LogItem(
                utils.generate_uuid(),
                resource,
                '{}.{}'.format(resource, action),
                diffed)


def _stage_changes(staged_resources, commited_resources, staged_log):

    for res_uid in staged_resources.keys():
        commited_data = commited_resources.get(res_uid, {})
        staged_data = staged_resources.get(res_uid, {})

        df = create_diff(staged_data, commited_data)

        if df:
            action = guess_action(commited_data, staged_data)
            log_item = create_logitem(res_uid, action, df)
            staged_log.append(log_item)
    return staged_log


def stage_changes():
    log = data.SL()
    log.clean()
    staged = {r.name: r.args for r in resource.load_all()}
    commited = data.CD()
    return _stage_changes(staged, commited, log)


def send_to_orchestration():
    dg = nx.MultiDiGraph()
    staged = {r.name: r.args for r in resource.load_all()}
    commited = data.CD()
    events = {}
    changed_nodes = []

    for res_uid in staged.keys():
        commited_data = commited.get(res_uid, {})
        staged_data = staged.get(res_uid, {})

        df = create_diff(staged_data, commited_data)

        if df:
            events[res_uid] = evapi.all_events(res_uid)
            changed_nodes.append(res_uid)
            action = guess_action(commited_data, staged_data)

            state_change = evapi.StateChange(res_uid, action)
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
    commited = data.CD()
    history = data.CL()
    for uid in uids:
        item = history.get(uid)
        res_db = resource.load(item.res)
        args_to_update = dictdiffer.revert(
            item.diff, commited.get(item.res, {}))
        res_db.update(args_to_update)


def revert(uid):
    return revert_uids([uid])

