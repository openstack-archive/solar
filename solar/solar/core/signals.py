# -*- coding: utf-8 -*-
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

import networkx

from solar.core.log import log
from solar.events.api import add_events
from solar.events.controls import Dependency
from solar.interfaces import orm


def guess_mapping(emitter, receiver):
    """Guess connection mapping between emitter and receiver.

    Suppose emitter and receiver have common inputs:
    ip, ssh_key, ssh_user

    Then we return a connection mapping like this:

    {
        'ip': '<receiver>.ip',
        'ssh_key': '<receiver>.ssh_key',
        'ssh_user': '<receiver>.ssh_user'
    }

    :param emitter:
    :param receiver:
    :return:
    """
    guessed = {}
    for key in emitter.args:
        if key in receiver.args:
            guessed[key] = key

    return guessed


def location_and_transports(emitter, receiver, orig_mapping):

    # XXX: we didn't agree on that reverse thign there

    def _remove_from_mapping(single):
        if single in orig_mapping:
            if isinstance(orig_mapping, dict):
                del orig_mapping[single]
            elif isinstance(orig_mapping, set):
                orig_mapping.remove(single)

    def _single(single, inps_emitter, inps_receiver):
        if inps_emitter and inps_receiver:
            log.debug("location and transports different, skipping")
            return
        emitter_single = emitter.db_obj.meta_inputs[single]
        receiver_single = receiver.db_obj.meta_inputs[single]
        emitter_single_reverse = emitter_single.get('reverse')
        receiver_single_reverse = receiver_single.get('reverse')
        # connect in other direction
        if emitter_single_reverse:
            if receiver_single_reverse:
                connect_single(receiver, single, emitter, single)
                _remove_from_mapping(single)
                return
        if receiver_single_reverse:
            connect_single(receiver, single, emitter, single)
            _remove_from_mapping(single)
            return
        if isinstance(orig_mapping, dict):
            orig_mapping[single] = single

    # XXX: that .args is slow on current backend
    # would be faster or another
    inps_emitter = emitter.args
    inps_receiver = receiver.args
    # XXX: should be somehow parametrized (input attribute?)
    for single in ('transports_id', 'location_id'):
        _single(single, inps_emitter[single], inps_receiver[single])
    return


def connect(emitter, receiver, mapping=None, events=None):
    if mapping is None:
        mapping = guess_mapping(emitter, receiver)

    # XXX: we didn't agree on that "reverse" there
    location_and_transports(emitter, receiver, mapping)

    if isinstance(mapping, set):
        mapping = {src: src for src in mapping}

    for src, dst in mapping.items():
        if not isinstance(dst, list):
            dst = [dst]

        for d in dst:
            connect_single(emitter, src, receiver, d)

    events_to_add = [
        Dependency(emitter.name, 'run', 'success', receiver.name, 'run'),
        Dependency(emitter.name, 'update', 'success', receiver.name, 'update')
    ]
    if isinstance(events, dict):
        for k, v in events.items():
            if v is not False:
                events_to_add = filter(lambda x: x.parent_action == k, events_to_add)
        add_events(emitter.name, events_to_add)
    elif events is not False:
        add_events(emitter.name, events_to_add)


def connect_single(emitter, src, receiver, dst):
    if ':' in dst:
        return connect_multi(emitter, src, receiver, dst)

    # Disconnect all receiver inputs
    # Check if receiver input is of list type first
    emitter_input = emitter.resource_inputs()[src]
    receiver_input = receiver.resource_inputs()[dst]

    if emitter_input.id == receiver_input.id:
        raise Exception(
            'Trying to connect {} to itself, this is not possible'.format(
                emitter_input.id)
        )

    if not receiver_input.is_list:
        receiver_input.receivers.delete_all_incoming(receiver_input)

    # Check for cycles
    # TODO: change to get_paths after it is implemented in drivers
    if emitter_input in receiver_input.receivers.as_set():
        raise Exception('Prevented creating a cycle on %s::%s' % (emitter.name,
                                                                  emitter_input.name))

    log.debug('Connecting {}::{} -> {}::{}'.format(
        emitter.name, emitter_input.name, receiver.name, receiver_input.name
    ))
    emitter_input.receivers.add(receiver_input)


def connect_multi(emitter, src, receiver, dst):
    receiver_input_name, receiver_input_key = dst.split(':')
    if '|' in receiver_input_key:
        receiver_input_key, receiver_input_tag = receiver_input_key.split('|')
    else:
        receiver_input_tag = None

    emitter_input = emitter.resource_inputs()[src]
    receiver_input = receiver.resource_inputs()[receiver_input_name]

    if not receiver_input.is_list or receiver_input_tag:
        receiver_input.receivers.delete_all_incoming(
            receiver_input,
            destination_key=receiver_input_key,
            tag=receiver_input_tag
        )

    # We can add default tag now
    receiver_input_tag = receiver_input_tag or emitter.name

    # NOTE: make sure that receiver.args[receiver_input] is of dict type
    if not receiver_input.is_hash:
        raise Exception(
            'Receiver input {} must be a hash or a list of hashes'.format(receiver_input_name)
        )

    log.debug('Connecting {}::{} -> {}::{}[{}], tag={}'.format(
        emitter.name, emitter_input.name, receiver.name, receiver_input.name,
        receiver_input_key,
        receiver_input_tag
    ))
    emitter_input.receivers.add_hash(
        receiver_input,
        receiver_input_key,
        tag=receiver_input_tag
    )


def disconnect_receiver_by_input(receiver, input_name):
    input_node = receiver.resource_inputs()[input_name]

    input_node.receivers.delete_all_incoming(input_node)


def disconnect(emitter, receiver):
    for emitter_input in emitter.resource_inputs().values():
        for receiver_input in receiver.resource_inputs().values():
            emitter_input.receivers.remove(receiver_input)


def detailed_connection_graph(start_with=None, end_with=None):
    resource_inputs_graph = orm.DBResource.inputs.graph()
    inputs_graph = orm.DBResourceInput.receivers.graph()

    def node_attrs(n):
        if isinstance(n, orm.DBResource):
            return {
                'color': 'yellowgreen',
                'style': 'filled',
            }
        elif isinstance(n, orm.DBResourceInput):
            return {
                'color': 'lightskyblue',
                'style': 'filled, rounded',
            }

    def format_name(i):
        if isinstance(i, orm.DBResource):
            return '"{}"'.format(i.name)
        elif isinstance(i, orm.DBResourceInput):
            return '{}/{}'.format(i.resource.name, i.name)

    for r, i in resource_inputs_graph.edges():
        inputs_graph.add_edge(r, i)

    ret = networkx.MultiDiGraph()

    for u, v in inputs_graph.edges():
        u_n = format_name(u)
        v_n = format_name(v)
        ret.add_edge(u_n, v_n)
        ret.node[u_n] = node_attrs(u)
        ret.node[v_n] = node_attrs(v)

    return ret
