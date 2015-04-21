# -*- coding: UTF-8 -*-
from collections import defaultdict
import itertools
import networkx as nx

import db

from x import utils


CLIENTS_CONFIG_KEY = 'clients-data-file'
CLIENTS = utils.read_config_file(CLIENTS_CONFIG_KEY)


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
    for key in emitter.requires:
        if key in receiver.requires:
            guessed[key] = key

    return guessed


def connect(emitter, receiver, mapping=None):
    guessed = guess_mapping(emitter, receiver)
    mapping = mapping or guessed

    for src, dst in mapping.items():
        # Disconnect all receiver inputs
        # Check if receiver input is of list type first
        if receiver.input_types.get(dst, '') != 'list':
            disconnect_receiver_by_input(receiver, dst)

        connect_src_dst(emitter, src, receiver, dst)

    receiver.save()
    utils.save_to_config_file(CLIENTS_CONFIG_KEY, CLIENTS)


def connect_src_dst(emitter, src, receiver, dst):
    CLIENTS.setdefault(emitter.name, {})
    CLIENTS[emitter.name].setdefault(src, [])
    CLIENTS[emitter.name][src].append((receiver.name, dst))

    # Copy emitter's values to receiver
    if src in emitter.args:
        receiver.update({dst: emitter.args[src]}, emitter=emitter)


def disconnect(emitter, receiver):
    for src, destinations in CLIENTS[emitter.name].items():
        destinations = [
            destination for destination in destinations
            if destination[0] == receiver.name
        ]

        for destination in destinations:
            receiver_input = destination[1]
            if receiver.input_types.get(receiver_input, '') == 'list':
                print 'Removing input {} from {}'.format(receiver_input, receiver.name)
                # TODO: update here? We're deleting an input...
                receiver.args[receiver_input] = {
                    k: v for k, v in receiver.args.get(receiver_input, {}).items()
                    if k != emitter.name
                }

        disconnect_by_src(emitter, src, receiver)

    # Inputs might have changed
    receiver.save()
    utils.save_to_config_file(CLIENTS_CONFIG_KEY, CLIENTS)


def disconnect_receiver_by_input(receiver, input):
    """Find receiver connection by input and disconnect it.

    :param receiver:
    :param input:
    :return:
    """
    for emitter_name, inputs in CLIENTS.items():
        emitter = db.get_resource(emitter_name)
        disconnect_by_src(emitter, input, receiver)


def disconnect_by_src(emitter, src, receiver):
    if src in CLIENTS[emitter.name]:
        CLIENTS[emitter.name][src] = [
            destination for destination in CLIENTS[emitter.name][src]
            if destination[0] != receiver.name
        ]


def notify(source, key, value):
    CLIENTS.setdefault(source.name, {})
    print 'Notify', source.name, key, value, CLIENTS[source.name]
    if key in CLIENTS[source.name]:
        for client, r_key in CLIENTS[source.name][key]:
            resource = db.get_resource(client)
            print 'Resource found', client
            if resource:
                resource.update({r_key: value}, emitter=source)
            else:
                print 'Resource {} deleted?'.format(client)
                pass


def assign_connections(receiver, connections):
    mappings = defaultdict(list)
    for key, dest in connections.iteritems():
        resource, r_key = dest.split('.')
        mappings[resource].append((r_key, key))
    for resource, r_mappings in mappings.iteritems():
        connect(resource, receiver, r_mappings)


def connection_graph():
    resource_dependencies = {}

    for source, destination_values in CLIENTS.items():
        resource_dependencies.setdefault(source, set())
        for src, destinations in destination_values.items():
            resource_dependencies[source].update([
                destination[0] for destination in destinations
            ])

    g = nx.DiGraph()

    # TODO: tags as graph node attributes
    for source, destinations in resource_dependencies.items():
        g.add_node(source)
        g.add_nodes_from(destinations)
        g.add_edges_from(
            itertools.izip(
                itertools.repeat(source),
                destinations
            )
        )

    return g
