#!/usr/bin/env python


import click
from solar.core.resource import virtual_resource as vr



@click.group()
def main():
    pass

class NailgunSource(object):

    def nodes(self, uids):
        from fuelclient.objects.node import Node
        nodes_obj = map(Node, nodes)
        return []

    def roles(self, roles):
        return []

    def master(self):
        return 'master', ''

class DumbSource(object):

    def nodes(self, uids):
        ip_mask = '10.0.0.%s'
        return [(uid, ip_mask % uid, 1) for uid in uids]

    def roles(self, uid):
        return 'primary-controller'

    def master(self):
        return 'master', '0.0.0.0'

source = DumbSource()

@main.command()
@click.argument('uids', nargs=-1)
def nodes(uids):
    master = source.master()
    vr.create('master', 'f2s/vrs/fuel_node.yaml',
        {'index': master[0], 'ip': master[1]})
    for uid, ip, env in source.nodes(uids):
        vr.create('fuel_node', 'f2s/vrs/fuel_node.yaml',
            {'index': uid, 'ip': ip})

@main.command()
@click.argument('uids', nargs=-1)
def basic(uids):
    master_index = source.master()[0]

    vr.create('genkeys', 'f2s/vrs/genkeys.yaml', {
        'node': 'node'+master_index,
        'index': master_index})
    for uid, ip, env in source.nodes(uids):
        vr.create('prep', 'f2s/vrs/prep.yaml',
            {'index': uid, 'env': env, 'node': 'node'+uid})


@main.command()
@click.argument('uids', nargs=-1)
def roles(uids):

    for uid, ip, env in source.nodes(uids):
        role = source.roles(uid)
        vr.create(role, 'f2s/vrs/'+role +'.yml',
            {'index': uid, 'env': env, 'node': 'node'+uid})


if __name__ == '__main__':
    main()
