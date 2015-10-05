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

    transports_for_solard.connect(solard_transport, {})
    ssh_transport.connect(transports_for_solard,{'ssh_key': 'transports:key',
                                                 'ssh_user': 'transports:user',
                                                 'ssh_port': 'transports:port',
                                                 'name': 'transports:name'})
    # set transports_id
    transports.connect(node, {})

    # it uses reverse mappings
    ssh_transport.connect(transports, {'ssh_key': 'transports:key',
                                        'ssh_user': 'transports:user',
                                        'ssh_port': 'transports:port',
                                        'name': 'transports:name'})
    solard_transport.connect(transports, {'solard_user': 'transports:user',
                                           'solard_port': 'transports:port',
                                           'solard_password': 'transports:password',
                                           'name': 'transports:name'})


    hosts = vr.create('hosts_file', 'resources/hosts_file', {})[0]
    node.connect(hosts, {
        'ip': 'hosts:ip',
        'name': 'hosts:name'
    })

    # for r in (node, hosts, ssh_transport, transports):
    #     print r.name, repr(r.args['location_id']), repr(r.args['transports_id'])

    # print hosts.transports()
    # print hosts.ip()

run()
