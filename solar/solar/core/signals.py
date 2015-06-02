# -*- coding: utf-8 -*-
import atexit
from collections import defaultdict
import itertools
import networkx as nx
import os

from solar import utils
from solar.interfaces.db import get_db

db = get_db()



CLIENTS_CONFIG_KEY = 'clients-data-file'
CLIENTS = utils.read_config_file(CLIENTS_CONFIG_KEY)


class Connections(object):
    @staticmethod
    def add(emitter, src, receiver, dst):
        if src not in emitter.args:
            return

        # TODO: implement general circular detection, this one is simple
        if [emitter.name, src] in CLIENTS.get(receiver.name, {}).get(dst, []):
            raise Exception('Attempted to create cycle in dependencies. Not nice.')

        CLIENTS.setdefault(emitter.name, {})
        CLIENTS[emitter.name].setdefault(src, [])
        if [receiver.name, dst] not in CLIENTS[emitter.name][src]:
            CLIENTS[emitter.name][src].append([receiver.name, dst])

        #utils.save_to_config_file(CLIENTS_CONFIG_KEY, CLIENTS)

    @staticmethod
    def remove(emitter, src, receiver, dst):
        CLIENTS[emitter.name][src] = [
            destination for destination in CLIENTS[emitter.name][src]
            if destination != [receiver.name, dst]
        ]

        #utils.save_to_config_file(CLIENTS_CONFIG_KEY, CLIENTS)

    @staticmethod
    def reconnect_all():
        """Reconstruct connections for resource inputs from CLIENTS.

        :return:
        """
        for emitter_name, dest_dict in CLIENTS.items():
            emitter = db.get_obj_resource(emitter_name)
            for emitter_input, destinations in dest_dict.items():
                for receiver_name, receiver_input in destinations:
                    receiver = db.get_obj_resource(receiver_name)
                    emitter.args[emitter_input].subscribe(
                        receiver.args[receiver_input])

    @staticmethod
    def clear():
        global CLIENTS

        CLIENTS = {}

        path = utils.read_config()[CLIENTS_CONFIG_KEY]
        if os.path.exists(path):
            os.remove(path)

    @staticmethod
    def flush():
        print 'FLUSHING Connections'
        utils.save_to_config_file(CLIENTS_CONFIG_KEY, CLIENTS)


atexit.register(Connections.flush)


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


def connect(emitter, receiver, mapping=None):
    mapping = mapping or guess_mapping(emitter, receiver)

    for src, dst in mapping.items():
        # Disconnect all receiver inputs
        # Check if receiver input is of list type first
        if receiver.args[dst].type_ != 'list':
            disconnect_receiver_by_input(receiver, dst)

        emitter.args[src].subscribe(receiver.args[dst])

    receiver.save()


def disconnect(emitter, receiver):
    for src, destinations in CLIENTS[emitter.name].items():
        disconnect_by_src(emitter.name, src, receiver)

        for destination in destinations:
            receiver_input = destination[1]
            if receiver_input in receiver.args:
                if receiver.args[receiver_input].type_ != 'list':
                    print 'Removing input {} from {}'.format(receiver_input, receiver.name)
                emitter.args[src].unsubscribe(receiver.args[receiver_input])


def disconnect_receiver_by_input(receiver, input):
    """Find receiver connection by input and disconnect it.

    :param receiver:
    :param input:
    :return:
    """
    for emitter_name, inputs in CLIENTS.items():
        emitter = db.get_resource(emitter_name)
        disconnect_by_src(emitter['id'], input, receiver)


def disconnect_by_src(emitter_name, src, receiver):
    if src in CLIENTS[emitter_name]:
        CLIENTS[emitter_name][src] = [
            destination for destination in CLIENTS[emitter_name][src]
            if destination[0] != receiver.name
        ]

    #utils.save_to_config_file(CLIENTS_CONFIG_KEY, CLIENTS)


def notify(source, key, value):
    CLIENTS.setdefault(source.name, {})
    print 'Notify', source.name, key, value, CLIENTS[source.name]
    if key in CLIENTS[source.name]:
        for client, r_key in CLIENTS[source.name][key]:
            resource = db.get_obj_resource(client)
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
        mappings[resource].append([r_key, key])
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


def detailed_connection_graph():
    g = nx.MultiDiGraph()

    for emitter_name, destination_values in CLIENTS.items():
        for emitter_input, receivers in CLIENTS[emitter_name].items():
            for receiver_name, receiver_input in receivers:
                label = emitter_input
                if emitter_input != receiver_input:
                    label = '{}:{}'.format(emitter_input, receiver_input)
                g.add_edge(emitter_name, receiver_name, label=label)

    return g
