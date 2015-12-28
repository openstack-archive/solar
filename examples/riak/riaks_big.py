#!/usr/bin/env python

# this allows you to create riak cluster as big as you want

import click
import sys

from solar.core import resource
from solar.core import signals
from solar.core import validation
from solar.core.resource import composer as cr
from solar import errors

from solar.interfaces.db import get_db

from solar.events.controls import React, Dep
from solar.events.api import add_event


db = get_db()


NODES = 3

def setup_riak(nodes_num=None, hosts_mapping=False):

    if nodes_num is None:
        nodes_num = NODES
    db.clear()

    resources = cr.create('nodes', 'templates/nodes', {'count': nodes_num})
    nodes = [x for x in resources if x.name.startswith('node')]
    hosts_services = [x for x in resources if x.name.startswith('hosts_file')]

    riak_services = []
    ips = '10.0.0.%d'
    for i in xrange(nodes_num):
        num = i + 1
        r = cr.create('riak_service%d' % num,
                      'resources/riak_node',
                      {'riak_self_name': 'riak%d' % num,
                       'riak_hostname': 'riak_server%d.solar' % num,
                       'riak_name': 'riak%d@riak_server%d.solar' % (num, num)})[0]
        riak_services.append(r)

    for i, riak in enumerate(riak_services):
        nodes[i].connect(riak)

    for i, riak in enumerate(riak_services[1:]):
        riak_services[0].connect(riak, {'riak_name': 'join_to'})

    if hosts_mapping:
        for riak in riak_services:
            for hosts_file in hosts_services:
                riak.connect_with_events(hosts_file,
                    {'riak_hostname': 'hosts:name',
                     'ip': 'hosts:ip'})

    res_errors = resource.validate_resources()
    for r, error in res_errors:
        click.echo('ERROR: %s: %s' % (r.name, error))
    has_errors = False

    if has_errors:
        click.echo("ERRORS")
        sys.exit(1)

    events = []
    for x in xrange(nodes_num):
        i = x + 1
        if hosts_mapping:
            events.append(Dep('hosts_file%d' % i, 'run', 'success', 'riak_service%d' % i, 'run'))
        if i >= 2:
            events.append(React('riak_service%d' % i, 'run', 'success', 'riak_service%d' % i, 'join'))
        events.append(React('riak_service%d' % i, 'join', 'success', 'riak_service1', 'commit'))

    for event in events:
        add_event(event)

    click.echo('Use solar changes process & orch')
    sys.exit(0)


@click.group()
def main():
    pass


@click.command()
@click.argument('nodes_count', type=int)
@click.argument('hosts_mapping', type=bool)
def deploy(nodes_count, hosts_mapping):
    click.secho("With big nodes_count, this example is DB heavy, it creates NxN connections, continue ? [y/N] ", fg='red', nl=False)
    c= click.getchar()
    if c in ('y', 'Y'):
        setup_riak(nodes_count, hosts_mapping)
    else:
        click.echo("Aborted")


if __name__ == '__main__':
    main.add_command(deploy)
    main()
