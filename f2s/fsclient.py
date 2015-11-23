#!/usr/bin/env python

import os

import click
from solar.core.resource import virtual_resource as vr
from solar.dblayer.model import ModelMeta



@click.group()
def main():
    pass

class NailgunSource(object):

    def nodes(self, uids):
        from fuelclient.objects.node import Node
        nodes_obj = map(Node, uids)
        return [(str(n.data['id']), str(n.data['ip']), str(n.data['cluster']))
                for n in nodes_obj]

    def roles(self, uid):
        from fuelclient.objects.node import Node
        node = Node(uid)
        return node.data['roles'] + node.data['pending_roles']

    def master(self):
        return 'master', '10.20.0.2'

class DumbSource(object):

    def nodes(self, uids):
        ip_mask = '10.0.0.%s'
        return [(uid, ip_mask % uid, 1) for uid in uids]

    def roles(self, uid):
        return ['primary-controller']

    def master(self):
        return 'master', '0.0.0.0'

if os.environ.get('DEBUG_FSCLIENT'):
    source = DumbSource()
else:
    source = NailgunSource()

@main.command()
@click.argument('uids', nargs=-1)
def nodes(uids):
    for uid, ip, env in source.nodes(uids):
        vr.create('fuel_node', 'f2s/vrs/fuel_node.yaml',
            {'index': uid, 'ip': ip})

@main.command()
@click.argument('env')
def master(env):
    master = source.master()
    vr.create('master', 'f2s/vrs/fuel_node.yaml',
        {'index': master[0], 'ip': master[1]})

    vr.create('genkeys', 'f2s/vrs/genkeys.yaml', {
        'node': 'node'+master[0],
        'index': env})

@main.command()
@click.argument('uids', nargs=-1)
def prep(uids):
    for uid, ip, env in source.nodes(uids):
        vr.create('prep', 'f2s/vrs/prep.yaml',
            {'index': uid, 'env': env, 'node': 'node'+uid})


@main.command()
@click.argument('uids', nargs=-1)
def roles(uids):

    for uid, ip, env in source.nodes(uids):
        for role in source.roles(uid):
            vr.create(role, 'f2s/vrs/'+role +'.yml',
                {'index': uid, 'env': env, 'node': 'node'+uid})


if __name__ == '__main__':
    main()
    ModelMeta.session_end()
