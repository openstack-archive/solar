#!/usr/bin/env python

# To run:
# example-lxc.py deploy
# solar changes stage
# solar changes process
# solar orch run-once last
# watch 'solar orch report last'

import click

from solar.core import signals
from solar.core.resource import virtual_resource as vr

from solar.interfaces.db import get_db

from solar.system_log import change
from solar.cli import orch

@click.group()
def main():
    pass


def lxc_template(idx):
    return {
        'user': 'root',
        'mgmt_ip': '172.18.11.{}'.format(idx),
        'container_name': 'test{}'.format(idx),
        'inventory_hostname': 'test{}'.format(idx),
        'properties':
            {'container_release': 'trusty'},
        'container_networks':
            {'mgmt': {
                'address': '172.18.11.{}'.format(idx), # address for container
                'bridge': 'br-int53', # bridge to attach veth pair
                'bridge_address': '172.18.11.253/24',
                'interface': 'eth1', # interface name in container
                'netmask': '255.255.255.0',
                'type': 'veth'}}
    }


@click.command()
def deploy():
    db = get_db()
    db.clear()
    signals.Connections.clear()

    node1 = vr.create('nodes', 'templates/nodes.yaml', {})[0]
    seed = vr.create('nodes', 'templates/seed_node.yaml', {})[0]

    ssh_key = vr.create('ssh_key1', 'resources/ssh_key', {
        'keys_dir': '/vagrant/.ssh',
        'private_key': '/vagrant/.ssh/id_rsa',
        'public_key': '/vagrant/.ssh/id_rsa.pub',
        'passphrase': '',
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

    lxc_hosts = range(28, 35)
    hosts_map = {}
    for idx in lxc_hosts:

        lxc_host_idx = vr.create(
            'lxc_host{}'.format(idx),
            'resources/lxc_container', lxc_template(idx))[0]
        hosts_map[idx] = lxc_host_idx

        signals.connect(node1, lxc_host_idx, {
            'ip': ['ansible_ssh_host', 'physical_host'],
            })
        # this is a required to introduce depends on relationship between lxc infre
        # and lxc container
        signals.connect(lxc_infra1, lxc_host_idx, {'provides': 'requires'})
        signals.connect(cnets2, lxc_host_idx)
        signals.connect(ssh_key, lxc_host_idx, {
            'public_key': 'pub_key',
            'private_key': 'user_key'})

    # RABBIT
    rabbitmq_service1 = vr.create('rabbitmq_service1', 'resources/rabbitmq_service/', {
        'management_port': 15672,
        'port': 5672,
    })[0]
    openstack_vhost = vr.create('openstack_vhost', 'resources/rabbitmq_vhost/', {
        'vhost_name': 'openstack'
    })[0]

    openstack_rabbitmq_user = vr.create('openstack_rabbitmq_user', 'resources/rabbitmq_user/', {
        'user_name': 'openstack',
        'password': 'openstack_password'
    })[0]

    signals.connect(hosts_map[28], rabbitmq_service1, {
        'mgmt_ip': 'ip',
        'user_key': 'ssh_key',
        'user': 'ssh_user'})
    signals.connect(rabbitmq_service1, openstack_vhost)
    signals.connect(rabbitmq_service1, openstack_rabbitmq_user)
    signals.connect(openstack_vhost, openstack_rabbitmq_user, {
        'vhost_name',
    })

    print change.send_to_orchestration()

main.add_command(deploy)


if __name__ == '__main__':
    main()
