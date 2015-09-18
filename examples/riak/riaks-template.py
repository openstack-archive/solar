#!/usr/bin/env python

# WARNING: this might not be most up-to-date script and not all things might
# work here, for most up-to-date version see example-riaks.py
# This is just a demo of the template language of Solar

import click
import sys

from solar.core import resource
from solar.interfaces.db import get_db
from solar import template


db = get_db()


def setup_riak():
    db.clear()

    nodes = template.nodes_from('templates/riak_nodes.yaml')

    riak_services = nodes.on_each(
        'resources/riak_node',
        args={
            'riak_self_name': 'riak{num}',
            'riak_hostname': 'riak_server{num}.solar',
            'riak_name': 'riak{num}@riak_server{num}.solar',
        }
    )

    slave_riak_services = riak_services.tail()

    riak_services.take(0).connect_list(
        slave_riak_services,
        mapping={
            'riak_name': 'join_to',
        }
    )

    hosts_files = nodes.on_each('resources/hosts_file')

    riak_services.connect_list_to_each(
        hosts_files,
        mapping={
            'ip': 'hosts:ip',
            'riak_hostname': 'hosts:name',
        },
        events=False
    )

    errors = resource.validate_resources()
    for r, error in errors:
        click.echo('ERROR: %s: %s' % (r.name, error))

    if errors:
        click.echo("ERRORS")
        sys.exit(1)

    hosts_files.add_deps('run/success', riak_services, 'run')
    slave_riak_services.add_reacts('run/success', slave_riak_services, 'join')
    slave_riak_services.add_reacts('leave/success', slave_riak_services, 'join')
    slave_riak_services.add_react('run/success', riak_services.take(0), 'commit')


def setup_haproxies():
    # TODO: VR loading needs to be supported, then we can do something like
    # nodes = template.load('nodes')

    nodes = template.ResourceListTemplate([
        resource.load('node1'),
        resource.load('node2'),
        resource.load('node3'),
    ])
    riak_services = template.ResourceListTemplate([
        resource.load('riak_node-0'),
        resource.load('riak_node-1'),
        resource.load('riak_node-2'),
    ])

    haproxy_services = nodes.on_each(
        'resources/haproxy_service'
    )
    haproxy_configs = nodes.on_each(
        'resources/haproxy_config'
    )
    haproxy_service_configs_http = riak_services.on_each(
        'resources/haproxy_service_config',
        {
            'listen_port': 8098,
            'protocol': 'http',
            'name': 'riak_haproxy_http{num}',
        }
    )
    haproxy_service_configs_pb = riak_services.on_each(
        'resources/haproxy_service_config',
        {
            'listen_port': 8087,
            'protocol': 'tcp',
            'name': 'riak_haproxy_pb{num}',
        }
    )

    riak_services.connect_list_to_each(
        haproxy_service_configs_http,
        {
            'riak_hostname': 'backends:server',
            'riak_port_http': 'backends:port',
        }
    )
    riak_services.connect_list_to_each(
        haproxy_service_configs_pb,
        {
            'riak_hostname': 'backends:server',
            'riak_port_pb': 'backends:port',
        }
    )
    haproxy_service_configs_http.connect_list(
        haproxy_configs,
        {
            'backends': 'config:backends',
            'listen_port': 'config:listen_port',
            'protocol': 'config:protocol',
            'name': 'config:name',
        }
    )
    haproxy_service_configs_pb.connect_list(
        haproxy_configs,
        {
            'backends': 'config:backends',
            'listen_port': 'config:listen_port',
            'protocol': 'config:protocol',
            'name': 'config:name',
        }
    )

    #nodes.add_reacts('run/success', haproxy_services, 'install')
    haproxy_services.add_deps('run/success', haproxy_configs, 'run')
    haproxy_configs.add_reacts('run/success', haproxy_services, 'apply_config')
    haproxy_configs.add_reacts('update/success', haproxy_services, 'apply_config')

    errors = resource.validate_resources()
    for r, error in errors:
        click.echo('ERROR: %s: %s' % (r.name, error))

    if errors:
        click.echo("ERRORS")
        sys.exit(1)


@click.group()
def main():
    pass


@click.command()
def deploy():
    setup_riak()


@click.command()
def add_haproxies():
    setup_haproxies()


@click.command()
def undeploy():
    raise NotImplemented("Not yet")


main.add_command(deploy)
main.add_command(undeploy)
main.add_command(add_haproxies)


if __name__ == '__main__':
    main()
