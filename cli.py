import click
import json
import networkx as nx

from x import resource as xr
from x import signals as xs


@click.group()
def cli():
    pass


def init_cli_resource():
    @click.group()
    def resource():
        pass

    cli.add_command(resource)

    @click.command()
    @click.argument('name')
    @click.argument('base_path')
    @click.argument('dest_path')
    @click.argument('args')
    def create(args, dest_path, base_path, name):
        print 'create', name, base_path, dest_path, args
        args = json.loads(args)
        xr.create(name, base_path, dest_path, args)

    resource.add_command(create)

    @click.command()
    @click.argument('path')
    def show(path):
        print xr.load(path)

    resource.add_command(show)


def init_cli_connect():
    @click.command()
    @click.argument('emitter')
    @click.argument('receiver')
    @click.option('--mapping', default=None)
    def connect(mapping, receiver, emitter):
        print 'Connect', emitter, receiver
        emitter = xr.load(emitter)
        receiver = xr.load(receiver)
        print emitter
        print receiver
        if mapping is not None:
            mapping = json.loads(mapping)
        xs.connect(emitter, receiver, mapping=mapping)

    cli.add_command(connect)

    @click.command()
    @click.argument('emitter')
    @click.argument('receiver')
    def disconnect(receiver, emitter):
        print 'Disconnect', emitter, receiver
        emitter = xr.load(emitter)
        receiver = xr.load(receiver)
        print emitter
        print receiver
        xs.disconnect(emitter, receiver)

    cli.add_command(disconnect)


def init_cli_connections():
    @click.group()
    def connections():
        pass

    cli.add_command(connections)

    @click.command()
    def show():
        print json.dumps(xs.CLIENTS, indent=2)

    connections.add_command(show)

    # TODO: this requires graphing libraries
    #@click.command()
    #def graph():
    #    nx.draw_graphviz(xs.connection_graph())

    #connections.add_command(graph)


if __name__ == '__main__':
    init_cli_resource()
    init_cli_connect()
    init_cli_connections()

    cli()
