#!/usr/bin/env python
import requests

from solar.core.resource import virtual_resource as vr
from solar.events.api import add_event
from solar.events.controls import React


discovery_service = 'http://0.0.0.0:8881'
bareon_service = 'http://0.0.0.0:9322/v1/nodes/{0}/partitioning'


class NodeAdapter(dict):

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    @property
    def safe_mac(self):
        return self['mac'].replace(':', '_')

    @property
    def partitioning(self):
        return requests.get(bareon_service.format(self['mac'])).json()

nodes_list = requests.get(discovery_service).json()

# Create slave node resources
node_resources = vr.create('nodes', 'templates/not_provisioned_nodes.yaml', {'nodes': nodes_list})

# Get master node
master_node = filter(lambda n: n.name == 'node_master', node_resources)[0]

# Dnsmasq resources
for node in nodes_list:
    node = NodeAdapter(node)
    node_resource = filter(lambda n: n.name.endswith('node_{0}'.format(node.safe_mac)), node_resources)[0]

    node_resource.update({'partitioning': node.partitioning})

    dnsmasq = vr.create('dnsmasq_{0}'.format(node.safe_mac), 'resources/dnsmasq', {})[0]
    master_node.connect(dnsmasq)
    node_resource.connect(dnsmasq, {'admin_mac': 'exclude_mac_pxe'})

    event = React(node_resource.name, 'run', 'success', node_resource.name, 'provision')
    add_event(event)
    event = React(node_resource.name, 'provision', 'success', dnsmasq.name, 'exclude_mac_pxe')
    add_event(event)
    event = React(dnsmasq.name, 'exclude_mac_pxe', 'success', node_resource.name, 'reboot')
    add_event(event)
