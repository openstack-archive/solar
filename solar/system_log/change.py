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
from solar.core import resource
from solar.core.resource.resource import RESOURCE_STATE
from solar.core import signals
from solar.dblayer.solar_models import CommitedResource
from solar.dblayer.solar_models import LogItem
from solar.dblayer.solar_models import StrInt
from solar.events import api as evapi
from solar.events.controls import StateChange
from solar.orchestration import graph
from solar.system_log import data
from solar import utils

from solar.system_log.consts import CHANGES


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

    def listify(t):
        # we need all values as lists, because we need the same behaviour
        # in pre and post save situations
        return list(map(listify, t)) if isinstance(t, (list, tuple)) else t

    res = tuple(dictdiffer.diff(commited, staged))
    return listify(res)


def create_logitem(resource, action, diffed, connections_diffed,
                   base_path=''):
    return LogItem.new(
        {'resource': resource,
         'action': action,
         'diff': diffed,
         'connections_diff': connections_diffed,
         'base_path': base_path,
         'log': 'staged'})


def create_sorted_diff(staged, commited):
    staged.sort()
    commited.sort()
    return create_diff(staged, commited)


def make_single_stage_item(resource_obj):
    commited = resource_obj.load_commited()
    base_path = resource_obj.base_path

    if resource_obj.to_be_removed():
        resource_args = {}
        resource_connections = []
    else:
        resource_args = resource_obj.args
        resource_connections = resource_obj.connections

    if commited.state == RESOURCE_STATE.removed.name:
        commited_args = {}
        commited_connections = []
    else:
        commited_args = commited.inputs
        commited_connections = commited.connections

    inputs_diff = create_diff(resource_args, commited_args)
    connections_diff = create_sorted_diff(
        resource_connections, commited_connections)

    # if new connection created it will be reflected in inputs
    # but using inputs to reverse connections is not possible
    if inputs_diff:
        li = create_logitem(
            resource_obj.name,
            guess_action(commited_args, resource_args),
            inputs_diff,
            connections_diff,
            base_path=base_path)
        li.save()
        return li
    return None


def stage_changes():
    for li in data.SL():
        li.delete()

    last = LogItem.history_last()
    since = StrInt.greater(last.updated) if last else None
    staged_log = utils.solar_map(make_single_stage_item,
                                 resource.load_updated(since), concurrency=10)
    staged_log = filter(None, staged_log)
    return staged_log


def send_to_orchestration():
    dg = nx.MultiDiGraph()
    events = {}
    changed_nodes = []

    for logitem in data.SL():
        events[logitem.resource] = evapi.all_events(logitem.resource)
        changed_nodes.append(logitem.resource)

        state_change = StateChange(logitem.resource, logitem.action)
        state_change.insert(changed_nodes, dg)

    evapi.build_edges(dg, events)

    # what `name` should be?
    dg.graph['name'] = 'system_log'
    return graph.create_plan_from_graph(dg)


def parameters(res, action, data):
    return {'args': [res, action],
            'type': 'solar_resource'}


def _get_args_to_update(args, connections):
    """Returns args to update

    For each resource we can update only args that are not provided
    by connections
    """
    inherited = [i[3].split(':')[0] for i in connections]
    return {
        key: args[key] for key in args
        if key not in inherited
    }


def revert_uids(uids):
    """Reverts uids

    :param uids: iterable not generator
    """
    items = LogItem.multi_get(uids)

    for item in items:

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
    """Resource should be created with all previous connections"""
    commited = CommitedResource.get(logitem.resource)
    args = dictdiffer.revert(logitem.diff, commited.inputs)
    connections = dictdiffer.revert(
        logitem.connections_diff, sorted(commited.connections))

    resource.Resource(logitem.resource, logitem.base_path,
                      args=_get_args_to_update(args, connections),
                      tags=commited.tags)
    for emitter, emitter_input, receiver, receiver_input in connections:
        emmiter_obj = resource.load(emitter)
        receiver_obj = resource.load(receiver)
        signals.connect(emmiter_obj, receiver_obj, {
                        emitter_input: receiver_input})


def _update_inputs_connections(res_obj, args, old_connections, new_connections):  # NOQA

    removed = []
    for item in old_connections:
        if item not in new_connections:
            removed.append(item)

    added = []
    for item in new_connections:
        if item not in old_connections:
            added.append(item)

    for emitter, _, receiver, _ in removed:
        emmiter_obj = resource.load(emitter)
        receiver_obj = resource.load(receiver)
        emmiter_obj.disconnect(receiver_obj)

    for emitter, emitter_input, receiver, receiver_input in added:
        emmiter_obj = resource.load(emitter)
        receiver_obj = resource.load(receiver)
        emmiter_obj.connect(receiver_obj, {emitter_input: receiver_input})

    if removed or added:
        # TODO without save we will get error
        # that some values can not be updated
        # even if connection was removed
        receiver_obj.db_obj.save()

    res_obj.update(args)


def _revert_update(logitem):
    """Revert of update should update inputs and connections"""
    res_obj = resource.load(logitem.resource)
    commited = res_obj.load_commited()

    connections = dictdiffer.revert(
        logitem.connections_diff, sorted(commited.connections))
    args = dictdiffer.revert(logitem.diff, commited.inputs)

    _update_inputs_connections(
        res_obj, _get_args_to_update(args, connections),
        commited.connections, connections)


def _revert_run(logitem):
    res_obj = resource.load(logitem.resource)
    res_obj.remove()


def revert(uid):
    return revert_uids([uid])


def _discard_remove(item):
    resource_obj = resource.load(item.resource)
    resource_obj.set_created()


def _discard_update(item):
    resource_obj = resource.load(item.resource)
    old_connections = resource_obj.connections
    new_connections = dictdiffer.revert(
        item.connections_diff, sorted(old_connections))
    args = dictdiffer.revert(item.diff, resource_obj.args)

    _update_inputs_connections(
        resource_obj, _get_args_to_update(args, new_connections),
        old_connections, new_connections)


def _discard_run(item):
    resource.load(item.resource).remove(force=True)


def discard_uids(uids):
    items = LogItem.multi_get(uids)
    for item in items:
        if item.action == CHANGES.update.name:
            _discard_update(item)
        elif item.action == CHANGES.remove.name:
            _discard_remove(item)
        elif item.action == CHANGES.run.name:
            _discard_run(item)
        else:
            log.debug('Action %s for resource %s is a side'
                      ' effect of another action', item.action, item.res)
        item.delete()


def discard_uid(uid):
    return discard_uids([uid])


def discard_all():
    staged_log = data.SL()
    return discard_uids([l.uid for l in staged_log])


def commit_all():
    """Helper mainly for ease of testing"""
    from solar.system_log.operations import move_to_commited
    for item in data.SL():
        move_to_commited(item.log_action)


def clear_history():
    LogItem.delete_all()
    CommitedResource.delete_all()
