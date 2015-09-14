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


def connect_single(emitter, src, receiver, dst):
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

    emitter_input.receivers.add(receiver_input)


def disconnect_receiver_by_input(receiver, input_name):
    input_node = receiver.resource_inputs()[input_name]

    input_node.receivers.delete_all_incoming(input_node)


def disconnect(emitter, receiver):
    for emitter_input in emitter.resource_inputs().values():
        for receiver_input in receiver.resource_inputs().values():
            emitter_input.receivers.remove(receiver_input)
