import time

from solar.core.resource import virtual_resource as vr
from solar import errors
from solar.dblayer.model import ModelMeta


def run():
    ModelMeta.remove_all()

    node = vr.create('node', 'resources/ro_node', {'name': 'first' + str(time.time()),
                                                   'ip': '10.0.0.3',
                                                   'node_id': 'node1',
                                                   })[0]

    transports = vr.create('transports_node1', 'resources/transports')[0]

    ssh_transport = vr.create('ssh_transport', 'resources/transport_ssh',
                              {'ssh_key': '/vagrant/.vagrant/machines/solar-dev1/virtualbox/private_key',
                               'ssh_user': 'vagrant'})[0]

    transports.connect(node, {})

    # it uses reverse mappings
    ssh_transport.connect(transports, {'ssh_key': 'transports:key',
                                       'ssh_user': 'transports:user',
                                       'ssh_port': 'transports:port',
                                       'name': 'transports:name'})

    hosts = vr.create('hosts_file', 'resources/hosts_file', {})[0]

    # let's add torrent transport for hosts file deployment (useless in real life)

    torrent_transport = vr.create('torrent_transport',
                                  'resources/transport_torrent',
                                  {'trackers': ['udp://open.demonii.com:1337',
                                                'udp://tracker.openbittorrent.com:80']})[0]
    # you could use any trackers as you want

    transports_for_torrent = vr.create(
        'transports_for_torrent', 'resources/transports')[0]

    transports_for_torrent.connect(torrent_transport, {})

    ssh_transport.connect_with_events(transports_for_torrent, {'ssh_key': 'transports:key',
                                                               'ssh_user': 'transports:user',
                                                               'ssh_port': 'transports:port',
                                                               'name': 'transports:name'},
                                      events={})

    transports_for_hosts = vr.create(
        'transports_for_hosts', 'resources/transports')[0]

    torrent_transport.connect(transports_for_hosts, {'trackers': 'transports:trackers',
                                                     'name': 'transports:name'})

    ssh_transport.connect(transports_for_hosts, {'ssh_key': 'transports:key',
                                                 'ssh_user': 'transports:user',
                                                 'ssh_port': 'transports:port',
                                                 'name': 'transports:name'})

    transports_for_hosts.connect(hosts)
    transports_for_hosts.connect_with_events(node, events={})

    node.connect(hosts, {
        'ip': 'hosts:ip',
        'name': 'hosts:name'
    })

run()
