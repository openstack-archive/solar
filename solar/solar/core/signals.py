# -*- coding: utf-8 -*-
from collections import defaultdict
import itertools
import networkx as nx

from solar.core.log import log
from solar.interfaces.db import get_db

db = get_db()


class Connections(object):
    @staticmethod
    def read_clients():
        """
        Returned structure is:

        emitter_name:
          emitter_input_name:
            - - dst_name
              - dst_input_name

        while DB structure is:

        emitter_name_key:
          emitter: emitter_name
          sources:
            emitter_input_name:
              - - dst_name
                - dst_input_name
        """

        ret = {}

        for data in db.get_list(collection=db.COLLECTIONS.connection):
            ret[data['emitter']] = data['sources']

        return ret

    @staticmethod
    def save_clients(clients):
        for emitter_name, sources in clients.items():
            data = {
                'emitter': emitter_name,
                'sources': sources,
            }
            db.save(emitter_name, data, collection=db.COLLECTIONS.connection)

    @staticmethod
    def add(emitter, src, receiver, dst):
        if src not in emitter.args:
            return

        clients = Connections.read_clients()

        # TODO: implement general circular detection, this one is simple
        if [emitter.name, src] in clients.get(receiver.name, {}).get(dst, []):
            raise Exception('Attempted to create cycle in dependencies. Not nice.')

        clients.setdefault(emitter.name, {})
        clients[emitter.name].setdefault(src, [])
        if [receiver.name, dst] not in clients[emitter.name][src]:
            clients[emitter.name][src].append([receiver.name, dst])

        Connections.save_clients(clients)

    @staticmethod
    def remove(emitter, src, receiver, dst):
        clients = Connections.read_clients()

        clients[emitter.name][src] = [
            destination for destination in clients[emitter.name][src]
            if destination != [receiver.name, dst]
        ]

        Connections.save_clients(clients)

    @staticmethod
    def receivers(emitter_name, emitter_input_name):
        return Connections.read_clients().get(emitter_name, {}).get(
            emitter_input_name, []
        )

    @staticmethod
    def emitter(receiver_name, receiver_input_name):
        for emitter_name, dest_dict in Connections.read_clients().items():
            for emitter_input_name, destinations in dest_dict.items():
                if [receiver_name, receiver_input_name] in destinations:
                    return [emitter_name, emitter_input_name]

    @staticmethod
    def clear():
        db.clear_collection(collection=db.COLLECTIONS.connection)


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

    #receiver.save()


def disconnect(emitter, receiver):
    clients = Connections.read_clients()

    for src, destinations in clients[emitter.name].items():
        for destination in destinations:
            receiver_input = destination[1]
            if receiver_input in receiver.args:
                if receiver.args[receiver_input].type_ != 'list':
                    log.debug(
                        'Removing input %s from %s', receiver_input, receiver.name
                    )
                emitter.args[src].unsubscribe(receiver.args[receiver_input])

        disconnect_by_src(emitter.name, src, receiver)


def disconnect_receiver_by_input(receiver, input):
    """Find receiver connection by input and disconnect it.

    :param receiver:
    :param input:
    :return:
    """
    clients = Connections.read_clients()

    for emitter_name, inputs in clients.items():
        disconnect_by_src(emitter_name, input, receiver)


def disconnect_by_src(emitter_name, src, receiver):
    clients = Connections.read_clients()

    if src in clients[emitter_name]:
        clients[emitter_name][src] = [
            destination for destination in clients[emitter_name][src]
            if destination[0] != receiver.name
        ]

    Connections.save_clients(clients)


def notify(source, key, value):
    from solar.core.resource import load

    clients = Connections.read_clients()

    clients.setdefault(source.name, {})
    Connections.save_clients(clients)

    log.debug('Notify %s %s %s %s', source.name, key, value, clients[source.name])
    if key in clients[source.name]:
        for client, r_key in clients[source.name][key]:
            resource = load(client)
            log.debug('Resource found: %s', client)
            if resource:
                resource.update({r_key: value}, emitter=source)
            else:
                log.debug('Resource %s deleted?', client)
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

    clients = Connections.read_clients()

    for source, destination_values in clients.items():
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

    clients = Connections.read_clients()

    for emitter_name, destination_values in clients.items():
        for emitter_input, receivers in clients[emitter_name].items():
            for receiver_name, receiver_input in receivers:
                label = emitter_input
                if emitter_input != receiver_input:
                    label = '{}:{}'.format(emitter_input, receiver_input)
                g.add_edge(emitter_name, receiver_name, label=label)

    return g
