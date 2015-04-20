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

    Suppose emitter and receiver have inputs:
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
    mapping = mapping or {}
    guessed = guess_mapping(emitter, receiver)
    guessed.update(mapping)

    for src, dst in guessed.items():
        CLIENTS.setdefault(emitter.name, {})
        CLIENTS[emitter.name].setdefault(src, [])
        CLIENTS[emitter.name][src].append((receiver.name, dst))

    utils.save_to_config_file(CLIENTS_CONFIG_KEY, CLIENTS)


def disconnect(emitter, receiver):
    for src, destinations in CLIENTS[emitter.name].items():
        CLIENTS[emitter.name][src] = [
            destination for destination in destinations
            if destination[0] != receiver.name
        ]

    utils.save_to_config_file(CLIENTS_CONFIG_KEY, CLIENTS)


def notify(source, key, value):
    CLIENTS.setdefault(source.name, [])
    print 'Notify', source.name, key, value, CLIENTS[source.name]
    if key in CLIENTS[source.name]:
        for client, r_key in CLIENTS[source.name][key]:
            resource = db.get_resource(client)
            print 'Resource found', client
            if resource:
                resource.update({r_key: value})
            else:
                print 'Resource {} deleted?'.format(client)
                pass


def assign_connections(receiver, connections):
    mappings = defaultdict(list)
    for key, dest in connections.iteritems():
        resource, r_key = dest.split('.')
        resource = db.get_resource(resource)
        value = resource.args[r_key]
        receiver.args[key] = value
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
