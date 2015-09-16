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

from solar.core.log import log
from solar.events.api import add_events
from solar.events.controls import Dependency


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


def connect(emitter, receiver, mapping={}, events=None):
    mapping = mapping or guess_mapping(emitter, receiver)

    if isinstance(mapping, set):
        for src in mapping:
            connect_single(emitter, src, receiver, src)
        return

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
    if emitter_input in receiver_input.receivers.value:
        raise Exception('Prevented creating a cycle')

    log.debug('Connecting {}::{} -> {}::{}'.format(
        emitter.name, emitter_input.name, receiver.name, receiver_input.name
    ))
    emitter_input.receivers.add(receiver_input)


def connect_multi(emitter, src, receiver, dst):
    receiver_input_name, receiver_input_key = dst.split(':')

    emitter_input = emitter.resource_inputs()[src]
    receiver_input = receiver.resource_inputs()[receiver_input_name]

    # NOTE: make sure that receiver.args[receiver_input] is of dict type
    if not receiver_input.is_hash:
        raise Exception(
            'Receiver input {} must be a hash or a list of hashes'.format(receiver_input_name)
        )

    log.debug('Connecting {}::{} -> {}::{}[{}]'.format(
        emitter.name, emitter_input.name, receiver.name, receiver_input.name,
        receiver_input_key
    ))
    emitter_input.receivers.add_hash(receiver_input, receiver_input_key)


def disconnect_receiver_by_input(receiver, input_name):
    input_node = receiver.resource_inputs()[input_name]

    input_node.receivers.delete_all_incoming(input_node)


def disconnect(emitter, receiver):
    for emitter_input in emitter.resource_inputs().values():
        for receiver_input in receiver.resource_inputs().values():
            emitter_input.receivers.remove(receiver_input)
