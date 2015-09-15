import click
import sys
import time

from solar.core import signals
from solar.core.resource import virtual_resource as vr

from solar.interfaces.db import get_db


db = get_db()


def run():
    db.clear()

    node1 = vr.create('node1', 'resources/ro_node', {'name': 'first' + str(time.time()),
                                                   'ip': '10.0.0.3',
                                                   'ssh_key': '/vagrant/.vagrant/machines/solar-dev1/virtualbox/private_key',
                                                   'ssh_user': 'vagrant'})[0]

    node2 = vr.create('node2', 'resources/ro_node', {'name': 'second' + str(time.time()),
                                                   'ip': '10.0.0.4',
                                                   'ssh_key': '/vagrant/.vagrant/machines/solar-dev2/virtualbox/private_key',
                                                   'ssh_user': 'vagrant'})[0]



    hosts1 = vr.create('hosts_file1', 'resources/hosts_file', {})[0]
    hosts2 = vr.create('hosts_file2', 'resources/hosts_file', {})[0]
    signals.connect(node1, hosts1, {
        'name': 'hosts_names',
        'ip': ['hosts_ips', 'ip'],
        'ssh_user': 'ssh_user',
        'ssh_key': 'ssh_key'
    })

    signals.connect(node2, hosts2, {
        'name': 'hosts_names',
        'ip': ['hosts_ips', 'ip'],
        'ssh_user': 'ssh_user',
        'ssh_key': 'ssh_key'
    })

    signals.connect(node1, hosts2, {
        'ip': 'hosts_ips',
        'name': 'hosts_names'
    })

    signals.connect(node2, hosts1, {
        'ip': 'hosts_ips',
        'name': 'hosts_names'
    })


run()
