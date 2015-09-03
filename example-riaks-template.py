#!/usr/bin/env python

# WARNING: this might not be most up-to-date script and not all things might
# work here, for most up-to-date version see example-riaks.py
# This is just a demo of the template language of Solar

from solar.interfaces.db import get_db
from solar.core import signals

db = get_db()
db.clear()
signals.Connections.clear()

from solar import template


nodes = template.nodes_from('templates/riak_nodes.yml')

riak_services = nodes.on_each(
    'resources/riak_node',
    {
        'riak_self_name': 'riak{num}',
        'riak_hostname': 'riak_server{num}.solar',
        'riak_name': 'riak{num}@riak_server{num}.solar',
})

slave_riak_services = riak_services.tail()

riak_services.take(0).connect_list(
    slave_riak_services,
    {
        'riak_name': 'join_to',
    }
)

hosts_files = nodes.on_each('resources/hosts_file')

riak_services.connect_list_to_each(
    hosts_files,
    {
        'ip': 'hosts_ips',
        'riak_hostname': 'hosts_names',
    },
    events=False
)


hosts_files.add_deps('run/success', riak_services, 'run')
slave_riak_services.add_reacts('run/success', slave_riak_services, 'join')
slave_riak_services.add_reacts('leave/success', slave_riak_services, 'join')
slave_riak_services.add_react('run/success', riak_services.take(0), 'commit')


haproxy_services = nodes.on_each(
    'resources/haproxy_service'
)
haproxy_configs = nodes.on_each(
    'resources/haproxy_config'
)
haproxy_service_configs_http = nodes.on_each(
    'resources/haproxy_service_config',
    {
        'listen_port': 8098,
        'protocol': 'http',
    }
)
haproxy_service_configs_pb = nodes.on_each(
    'resources/haproxy_service_config',
    {
        'listen_port': 8087,
        'protocol': 'tcp',
    }
)

riak_services.connect_list_to_each(
    haproxy_service_configs_http,
    {
        'riak_hostname': 'servers',
        'riak_port_http': 'ports',
    }
)
riak_services.connect_list_to_each(
    haproxy_service_configs_pb,
    {
        'riak_hostname': 'servers',
        'riak_port_pb': 'ports',
    }
)
haproxy_service_configs_http.connect_list(
    haproxy_configs,
    {
        'protocol': 'configs_protocols',
        'listen_port': 'listen_ports',
        'name': 'configs_names',
        'servers': 'configs',
        'ports': 'configs_ports',
    }
)
haproxy_service_configs_pb.connect_list(
    haproxy_configs,
    {
        'protocol': 'configs_protocols',
        'listen_port': 'listen_ports',
        'name': 'configs_names',
        'servers': 'configs',
        'ports': 'configs_ports',
    }
)
haproxy_configs.connect_list(
    haproxy_services,
    {
        'listen_ports': 'ports',
    }
)

nodes.add_reacts('run/success', haproxy_services, 'install')
haproxy_services.add_deps('install/success', haproxy_configs, 'run')
haproxy_configs.add_reacts('run/success', haproxy_services, 'run')
haproxy_configs.add_reacts('update/success', haproxy_services, 'update')
