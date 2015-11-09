#!/usr/bin/env python
import requests

from solar.core.resource import virtual_resource as vr
from solar.events.api import add_event
from solar.events.controls import React


discovery_service = 'http://0.0.0.0:8881'
bareon_service = 'http://0.0.0.0:9322/v1/nodes/{0}/partitioning'
bareon_sync = 'http://0.0.0.0:9322/v1/actions/sync_all'


class NodeAdapter(dict):

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    @property
    def node_id(self):
        return self['id']

    @property
    def partitioning(self):
        return requests.get(bareon_service.format(self['id'])).json()

# Sync hw info about nodes from discovery service into bareon-api
requests.post(bareon_sync)

# Get list of nodes from discovery service
nodes_list = requests.get(discovery_service).json()

# Create slave node resources
node_resources = vr.create('nodes', 'templates/not_provisioned_nodes.yaml',
                           {'nodes': nodes_list})

# Get master node
master_node = filter(lambda n: n.name == 'node_master', node_resources)[0]

with open('/vagrant/tmp/keys/ssh_public') as fp:
    master_key = fp.read().strip()

# Dnsmasq resources
for node in nodes_list:
    node = NodeAdapter(node)
    node_resource = next(n for n in node_resources
                         if n.name.endswith('node_{0}'.format(node.node_id)))

    node_resource.update(
        {
            'partitioning': node.partitioning,
            'master_key': master_key,
        }
    )

    dnsmasq = vr.create('dnsmasq_{0}'.format(node.node_id),
                        'resources/dnsmasq', {})[0]
    master_node.connect(dnsmasq)
    node_resource.connect(dnsmasq, {'admin_mac': 'exclude_mac_pxe'})

    event = React(node_resource.name, 'run', 'success', node_resource.name,
                  'provision')
    add_event(event)
    event = React(node_resource.name, 'provision', 'success', dnsmasq.name,
                  'exclude_mac_pxe')
    add_event(event)
    event = React(dnsmasq.name, 'exclude_mac_pxe', 'success',
                  node_resource.name, 'reboot')
    add_event(event)
