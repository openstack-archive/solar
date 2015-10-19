#!/usr/bin/env python

import requests

from solar.core import resource
from solar.core import signals
from solar.core import validation
from solar.core.resource import virtual_resource as vr

from solar.events.controls import React
from solar.events.api import add_event


discovery_service = 'http://0.0.0.0:8881'

# DEBUG use a single node
nodes_list = [requests.get(discovery_service).json()[0]]


# Create slave node resources
node_resources = vr.create('nodes', 'templates/not_provisioned_nodes.yaml', {'nodes': nodes_list})

# Get master node
master_node = filter(lambda n: n.name == 'node_master', node_resources)[0]

# Dnsmasq resources
for node in nodes_list:
    dnsmasq = vr.create('dnsmasq_{0}'.format(node['mac'].replace(':', '_')), 'resources/dnsmasq', {})[0]
    node = filter(lambda n: n.name.endswith('node{0}'.format(node['mac']).replace(':', '_')), node_resources)[0]
    master_node.connect(dnsmasq)
    node.connect(dnsmasq, {'admin_mac': 'exclude_mac_pxe'})

    event = React(node.name, 'run', 'success', node.name, 'provision')
    add_event(event)
    event = React(node.name, 'provision', 'success', dnsmasq.name, 'exclude_mac_pxe')
    add_event(event)
    event = React(dnsmasq.name, 'exclude_mac_pxe', 'success', node.name, 'reboot')
    add_event(event)
