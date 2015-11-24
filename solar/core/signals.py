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
from solar.dblayer.solar_models import Resource as DBResource


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

    for key in emitter.db_obj.meta_inputs:
        if key in receiver.db_obj.meta_inputs:
            guessed[key] = key
    return guessed


def location_and_transports(emitter, receiver, orig_mapping):

    # XXX: we definitely need to change this
    # inputs shouldn't carry is_own, or is_emit flags
    # but for now we don't have anything better

    def _remove_from_mapping(single):
        if single in orig_mapping:
            if isinstance(orig_mapping, dict):
                del orig_mapping[single]
            elif isinstance(orig_mapping, set):
                orig_mapping.remove(single)

    def _single(single, emitter, receiver, inps_emitter, inps_receiver):
        # this function is responsible for doing magic with transports_id and location_id
        # it tries to be safe and smart as possible
        # it connects only when 100% that it can and should
        # user can always use direct mappings,
        # we also use direct mappings in VR
        # when we will remove location_id and transports_id from inputs then this function,
        #     will be deleted too
        if inps_emitter and inps_receiver:
            if not inps_emitter == inps_receiver:
                if not '::' in inps_receiver:
                    pass
                    # log.warning("Different %r defined %r => %r", single, emitter.name, receiver.name)
                return
            else:
                # log.debug("The same %r defined for %r => %r, skipping", single, emitter.name, receiver.name)
                return
        emitter_single = emitter.db_obj.meta_inputs[single]
        receiver_single = receiver.db_obj.meta_inputs[single]
        emitter_single_reverse = emitter_single.get('reverse')
        receiver_single_reverse = receiver_single.get('reverse')
        if inps_receiver is None and inps_emitter is not None:
            # we don't connect automaticaly when receiver is None and emitter is not None
            # for cases when we connect existing transports to other data containers
            if receiver_single_reverse:
                log.info("Didn't connect automaticaly %s::%s -> %s::%s",
                         receiver.name,
                         single,
                         emitter.name,
                         single)
                return
        if emitter_single.get('is_emit') is False:
            # this case is when we connect resource to transport itself
            # like adding ssh_transport for solar_agent_transport and we don't want then
            # transports_id to be messed
            # it forbids passing this value around
            # log.debug("Disabled %r mapping for %r", single, emitter.name)
            return
        if receiver_single.get('is_own') is False:
            # this case is when we connect resource which has location_id but that is
            # from another resource
            log.debug("Not is_own %r for %r ", single, emitter.name)
            return
        # connect in other direction
        if emitter_single_reverse:
            if receiver_single_reverse:
                # TODO: this should be moved to other place
                receiver._connect_inputs(emitter, {single: single})
                _remove_from_mapping(single)
                return
        if receiver_single_reverse:
            # TODO: this should be moved to other place
            receiver._connect_inputs(emitter, {single: single})
            _remove_from_mapping(single)
            return
        if isinstance(orig_mapping, dict):
            orig_mapping[single] = single

    # XXX: that .args is slow on current backend
    # would be faster or another
    inps_emitter = emitter.db_obj.inputs
    inps_receiver = receiver.db_obj.inputs
    # XXX: should be somehow parametrized (input attribute?)
    # with dirty_state_ok(DBResource, ('index', )):
    for single in ('transports_id', 'location_id'):
        if single in inps_emitter and single in inps_receiver:
            _single(single, emitter, receiver, inps_emitter[single], inps_receiver[single])
        else:
            log.warning('Unable to create connection for %s with'
                        ' emitter %s, receiver %s',
                        single, emitter.name, receiver.name)
    return


def get_mapping(emitter, receiver, mapping=None):
    if mapping is None:
        mapping = guess_mapping(emitter, receiver)
    location_and_transports(emitter, receiver, mapping)
    return mapping


def connect(emitter, receiver, mapping=None):
    emitter.connect(receiver, mapping)


def disconnect_receiver_by_input(receiver, input_name):
    # input_node = receiver.resource_inputs()[input_name]

    # input_node.receivers.delete_all_incoming(input_node)
    receiver.db_obj.inputs.disconnect(input_name)


def detailed_connection_graph(start_with=None, end_with=None, details=False):
    from solar.core.resource import Resource, load_all

    if details:
        def format_for_edge(resource, input):
            return '"{}/{}"'.format(resource, input)
    else:
        def format_for_edge(resource, input):
            input = input.split(':', 1)[0]
            return '"{}/{}"'.format(resource, input)

    res_props = {'color': 'yellowgreen',
                 'style': 'filled'}
    inp_props = {'color': 'lightskyblue',
                 'style': 'filled, rounded'}

    graph = networkx.DiGraph()

    resources = load_all()

    for resource in resources:
        res_node = '{}'.format(resource.name)
        for name in resource.db_obj.meta_inputs:
            resource_input = format_for_edge(resource.name, name)
            graph.add_edge(resource.name, resource_input)
            graph.node[resource_input] = inp_props
        conns = resource.connections
        for (emitter_resource, emitter_input, receiver_resource, receiver_input) in conns:
            e = format_for_edge(emitter_resource, emitter_input)
            r = format_for_edge(receiver_resource, receiver_input)
            graph.add_edge(emitter_resource, e)
            graph.add_edge(receiver_resource, r)
            graph.add_edge(e, r)
            graph.node[e] = inp_props
            graph.node[r] = inp_props
        graph.node[res_node] = res_props
    return graph
