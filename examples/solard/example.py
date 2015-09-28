import click
import sys
import time

from solar.core import resource
from solar.core import signals
from solar.core.resource import virtual_resource as vr

from solar.interfaces.db import get_db


db = get_db()



def run():
    db.clear()

    node = vr.create('node', 'resources/ro_node', {'name': 'first' + str(time.time()),
                                                       'ip': '10.0.0.3',
                                                       'node_id': 'node1',
                                                   })[0]

    transports = vr.create('transports_node1', 'resources/transports')[0]
    transports_for_solard = vr.create('transports_for_solard', 'resources/transports')[0]

    ssh_transport  = vr.create('ssh_transport', 'resources/transport_ssh',
                               {'ssh_key': '/vagrant/.vagrant/machines/solar-dev1/virtualbox/private_key',
                                'ssh_user': 'vagrant'})[0]

    solard_transport  = vr.create('solard_transport', 'resources/transport_solard',
                                  {'solard_user': 'vagrant',
                                   'solard_password': 'password'})[0]

    signals.connect(transports_for_solard, solard_transport, {})

    signals.connect(ssh_transport, transports_for_solard, {'ssh_key': 'transports:key',
                                                               'ssh_user': 'transports:user',
                                                               'ssh_port': 'transports:port',
                                                               'name': 'transports:name'})
    # set transports_id
    signals.connect(transports, node, {})

    # it uses reverse mappings
    signals.connect(ssh_transport, transports, {'ssh_key': 'transports:key',
                                                'ssh_user': 'transports:user',
                                                'ssh_port': 'transports:port',
                                                'name': 'transports:name'})

    signals.connect(solard_transport, transports, {'solard_user': 'transports:user',
                                                   'solard_port': 'transports:port',
                                                   'solard_password': 'transports:password',
                                                   'name': 'transports:name'})


    hosts = vr.create('hosts_file', 'resources/hosts_file', {})[0]
    signals.connect(node, hosts, {
        'ip': 'hosts:ip',
        'name': 'hosts:name'
    })

    # for r in (node, hosts, ssh_transport, transports):
    #     print r.name, repr(r.args['location_id']), repr(r.args['transports_id'])

    # print hosts.transports()
    # print hosts.ip()

run()
