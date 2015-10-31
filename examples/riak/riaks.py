#!/usr/bin/env python

# To run:
# python example-riaks.py deploy
# solar changes stage
# solar changes process
# solar orch run-once last
# python example-riaks.py add_haproxies
# solar changes stage
# solar changes process
# solar orch run-once last


import click
import sys

from solar.core import resource
from solar.core import signals
from solar.core import validation
from solar.core.resource import virtual_resource as vr
from solar import errors

from solar.dblayer.model import ModelMeta

from solar.interfaces.db import get_db

from solar.events.controls import React, Dep
from solar.events.api import add_event

from solar.dblayer.solar_models import Resource

# db = get_db()


def setup_riak():
    # db.clear()

    ModelMeta.remove_all()
    resources = vr.create('nodes', 'templates/nodes.yaml', {'count': 3})
    nodes = [x for x in resources if x.name.startswith('node')]
    node1, node2, node3 = nodes
    hosts_services = [x for x in resources if x.name.startswith('hosts_file')]

    riak_services = []
    ips = '10.0.0.%d'
    for i in xrange(3):
        num = i + 1
        r = vr.create('riak_service%d' % num,
                      'resources/riak_node',
                      {'riak_self_name': 'riak%d' % num,
                       'storage_backend': 'leveldb',
                       'riak_hostname': 'riak_server%d.solar' % num,
                       'riak_name': 'riak%d@riak_server%d.solar' % (num, num)})[0]
        riak_services.append(r)

    for i, riak in enumerate(riak_services):
        nodes[i].connect(riak)

    for i, riak in enumerate(riak_services[1:]):
        riak_services[0].connect(riak, {'riak_name': 'join_to'})

    for riak in riak_services:
        for hosts_file in hosts_services:
            riak.connect_with_events(hosts_file,
                {'riak_hostname': 'hosts:name',
                 'ip': 'hosts:ip'})

    Resource.save_all_lazy()
    errors = resource.validate_resources()
    for r, error in errors:
        click.echo('ERROR: %s: %s' % (r.name, error))
    has_errors = False

    if errors:
        click.echo("ERRORS")
        sys.exit(1)

    events = [
        Dep('hosts_file1', 'run', 'success', 'riak_service1', 'run'),
        Dep('hosts_file2', 'run', 'success', 'riak_service2', 'run'),
        Dep('hosts_file3', 'run', 'success', 'riak_service3', 'run'),

        React('riak_service2', 'run', 'success', 'riak_service2', 'join'),
        React('riak_service3', 'run', 'success', 'riak_service3', 'join'),

        # Dep('riak_service1', 'run', 'success', 'riak_service2', 'join'),
        # Dep('riak_service1', 'run', 'success', 'riak_service3', 'join'),

        # React('riak_service2', 'join', 'error', 'riak_service2', 'leave'),
        # React('riak_service3', 'join', 'error', 'riak_service3', 'leave'),

        React('riak_service2', 'leave', 'success', 'riak_service2', 'join'),
        React('riak_service3', 'leave', 'success', 'riak_service3', 'join'),

        # React('riak_service2', 'leave', 'success', 'riak_service1', 'commit_leave'),
        # React('riak_service3', 'leave', 'success', 'riak_service1', 'commit_leave'),

        # Dep('riak_service1', 'commit_leave', 'success', 'riak_service2', 'join'),
        # Dep('riak_service1', 'commit_leave', 'success', 'riak_service3', 'join'),

        React('riak_service3', 'join', 'success', 'riak_service1', 'commit'),
        React('riak_service2', 'join', 'success', 'riak_service1', 'commit')
    ]

    for event in events:
        add_event(event)

    click.echo('Use solar changes process & orch')
    sys.exit(0)


def setup_haproxies():
    hps = []
    hpc = []
    hpsc_http = []
    hpsc_pb = []
    for i in xrange(3):
        num = i + 1
        hps.append(vr.create('haproxy_service%d' % num,
                             'resources/haproxy_service',
                             {})[0])
        hpc.append(vr.create('haproxy_config%d' % num,
                             'resources/haproxy_config',
                             {})[0])
        hpsc_http.append(vr.create('haproxy_service_config_http%d' % num,
                                   'resources/haproxy_service_config',
                                   {'listen_port': 8098,
                                    'protocol': 'http',
                                    'name': 'riak_haproxy_http%d' % num})[0])
        hpsc_pb.append(vr.create('haproxy_service_config_pb%d' % num,
                                 'resources/haproxy_service_config',
                                 {'listen_port': 8087,
                                  'protocol': 'tcp',
                                  'name': 'riak_haproxy_pb%d' % num})[0])

    riak1 = resource.load('riak_service1')
    riak2 = resource.load('riak_service2')
    riak3 = resource.load('riak_service3')
    riaks = [riak1, riak2, riak3]

    for single_hpsc in hpsc_http:
        for riak in riaks:
            riak.connect(single_hpsc, {
                'riak_hostname': 'backends:server',
                'riak_port_http': 'backends:port'})

    for single_hpsc in hpsc_pb:
        for riak in riaks:
            riak.connect(single_hpsc,
                {'riak_hostname': 'backends:server',
                 'riak_port_pb': 'backends:port'})

    # haproxy config to haproxy service

    for single_hpc, single_hpsc in zip(hpc, hpsc_http):
        single_hpsc.connect(single_hpc, {"backends": "config:backends",
                                                  "listen_port": "config:listen_port",
                                                  "protocol": "config:protocol",
                                                  "name": "config:name"})

    for single_hpc, single_hpsc in zip(hpc, hpsc_pb):
        single_hpsc.connect(single_hpc, {"backends": "config:backends",
                                                  "listen_port": "config:listen_port",
                                                  "protocol": "config:protocol",
                                                  "name": "config:name"})


    # assign haproxy services to each node

    node1 = resource.load('node1')
    node2 = resource.load('node2')
    node3 = resource.load('node3')
    nodes = [node1, node2, node3]

    for single_node, single_hps in zip(nodes, hps):
        single_node.connect(single_hps)

    for single_node, single_hpc in zip(nodes, hpc):
        single_node.connect(single_hpc)

    has_errors = False
    for r in locals().values():

        # TODO: handle list
        if not isinstance(r, resource.Resource):
            continue

        # print 'Validating {}'.format(r.name)
        local_errors = validation.validate_resource(r)
        if local_errors:
            has_errors = True
            print 'ERROR: %s: %s' % (r.name, local_errors)

    if has_errors:
        print "ERRORS"
        sys.exit(1)

    events = []
    for node, single_hps, single_hpc in zip(nodes, hps, hpc):
        # r = React(node.name, 'run', 'success', single_hps.name, 'install')
        d = Dep(single_hps.name, 'run', 'success', single_hpc.name, 'run')
        e1 = React(single_hpc.name, 'run', 'success', single_hps.name, 'apply_config')
        e2 = React(single_hpc.name, 'update', 'success', single_hps.name, 'apply_config')
        # events.extend([r, d, e1, e2])
        events.extend([d, e1, e2])

    for event in events:
        add_event(event)


@click.command()
@click.argument('i', type=int, required=True)
def add_solard(i):
    solard_transport  = vr.create('solard_transport%s' % i, 'resources/transport_solard',
                                  {'solard_user': 'vagrant',
                                   'solard_password': 'password'})[0]
    transports = resource.load('transports%s' % i)
    ssh_transport = resource.load('ssh_transport%s' % i)
    transports_for_solard = vr.create('transports_for_solard%s' % i, 'resources/transports')[0]

    # install solard with ssh
    signals.connect(transports_for_solard, solard_transport, {})

    signals.connect(ssh_transport, transports_for_solard, {'ssh_key': 'transports:key',
                                                           'ssh_user': 'transports:user',
                                                           'ssh_port': 'transports:port',
                                                           'name': 'transports:name'})

    # add solard to transports on this node
    signals.connect(solard_transport, transports, {'solard_user': 'transports:user',
                                                   'solard_port': 'transports:port',
                                                   'solard_password': 'transports:password',
                                                   'name': 'transports:name'})


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
main.add_command(add_solard)


if __name__ == '__main__':
    main()
