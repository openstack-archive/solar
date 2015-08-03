import click
import sys
import time

from solar.core import actions
from solar.core import resource
from solar.core import signals
from solar.core import validation
from solar.core.resource import virtual_resource as vr
from solar import errors

from solar.interfaces.db import get_db


@click.group()
def main():
    pass


@click.command()
def deploy():
    db = get_db()
    db.clear()
    signals.Connections.clear()

    node1 = vr.create('nodes', 'templates/nodes.yml', {})[0]
    seed = vr.create('nodes', 'templates/seed_node.yml', {})[0]

    ssh_key = vr.create('ssh_key1', 'resources/ssh_key', {
        'path': '/vagrant/.ssh/id_rsa',
        'pub_path': '/vagrant/.ssh/id_rsa.pub'
    })[0]
    signals.connect(seed, ssh_key)

    cnets1 = vr.create('cnets1', 'resources/container_networks', {
        'networks':
            {'mgmt': {
                'bridge': 'br-int53',
                'bridge_address': '172.18.11.254/24'
            }}
        })[0]
    cnets2 = vr.create('cnets2', 'resources/container_networks', {
        'networks':
            {'mgmt': {
                'bridge': 'br-int53',
                'bridge_address': '172.18.11.253/24'
            }}
        })[0]
    signals.connect(seed, cnets1)
    signals.connect(node1, cnets2)

    vxlan_mesh1 = vr.create('vxlan_mesh1', 'resources/vxlan_mesh', {
        'id': 53,
        'parent': 'eth1',
        'master': 'br-int53'
    })[0]
    vxlan_mesh2 = vr.create('vxlan_mesh2', 'resources/vxlan_mesh', {
        'id': 53,
        'parent': 'eth1',
        'master': 'br-int53'
    })[0]
    # seed node should be connected anyway, because we need to be able to ssh
    # into containers from any node
    signals.connect(seed, vxlan_mesh1)
    signals.connect(node1, vxlan_mesh2)

    lxc_infra1 = vr.create('lxc_infra1', 'resources/lxc_host', {})[0]
    signals.connect(node1, lxc_infra1)

    lxc_host1 = vr.create('lxc_host1', 'resources/lxc_container', {
        'container_name': 'test13',
        'inventory_hostname': 'test13',
        'properties':
            {'container_release': 'trusty'},
        'container_networks':
            {'mgmt': {
                'address': '172.18.11.2', # address for container
                'bridge': 'br-int53', # bridge to attach veth pair
                'bridge_address': '172.18.11.253/24',
                'interface': 'eth1', # interface name in container
                'netmask': '255.255.255.0',
                'type': 'veth'}}
        })[0]
    signals.connect(node1, lxc_host1, {
        'ip': ['ansible_ssh_host', 'physical_host'],
        })
    # this is a required to introduce depends on relationship between lxc infre
    # and lxc container
    signals.connect(lxc_infra1, lxc_host1, {'provides': 'requires'})
    signals.connect(cnets2, lxc_host1)
    signals.connect(ssh_key, lxc_host1, {'pub_path': 'pub_key'})

main.add_command(deploy)


if __name__ == '__main__':
    main()

