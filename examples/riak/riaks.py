# To run:
# python example-riaks.py deploy
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

from solar.interfaces.db import get_db

from solar.events.controls import React, Dep
from solar.events.api import add_event


db = get_db()


def setup_riak():
    db.clear()

    nodes = vr.create('nodes', 'templates/riak_nodes.yaml', {})
    node1, node2, node3 = nodes

    riak_services = []
    ips = '10.0.0.%d'
    for i in xrange(3):
        num = i + 1
        r = vr.create('riak_service%d' % num,
                      'resources/riak_node',
                      {'riak_self_name': 'riak%d' % num,
                       'riak_hostname': 'riak_server%d.solar' % num,
                       'riak_name': 'riak%d@riak_server%d.solar' % (num, num)})[0]
        riak_services.append(r)

    for i, riak in enumerate(riak_services):
        signals.connect(nodes[i], riak)

    for i, riak in enumerate(riak_services[1:]):
        signals.connect(riak_services[0], riak, {'riak_name': 'join_to'}, events=None)

    hosts_services = []
    for i, riak in enumerate(riak_services):
        num = i + 1
        hosts_file = vr.create('hosts_file%d' % num,
                               'resources/hosts_file', {})[0]
        hosts_services.append(hosts_file)
        signals.connect(nodes[i], hosts_file)

    for riak in riak_services:
        for hosts_file in hosts_services:
            signals.connect(riak, hosts_file,
                            {'riak_hostname': 'hosts:name',
                             'ip': 'hosts:ip'},
                            events=False)

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

    print 'Use solar changes process & orch'
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
            # signals.connect(riak, single_hpsc, {'riak_hostname': 'servers',
            #                                     'riak_port_http': 'ports'})
            signals.connect(riak, single_hpsc, {'riak_hostname': 'backends:server',
                                                'riak_port_http': 'backends:port'})

    for single_hpsc in hpsc_pb:
        for riak in riaks:
            # signals.connect(riak, single_hpsc, {'riak_hostname': 'servers',
            #                                     'riak_port_pb': 'ports'})
            signals.connect(riak, single_hpsc, {'riak_hostname': 'backends:server',
                                                'riak_port_pb': 'backends:port'})

    # haproxy config to haproxy service

    for single_hpc, single_hpsc in zip(hpc, hpsc_http):
        # signals.connect(single_hpsc, single_hpc, {'protocol': 'configs_protocols',
        #                                           'listen_port': 'listen_ports',
        #                                           'name': 'configs_names',
        #                                           'servers': 'configs',
        #                                           'ports': 'configs_ports'})
        signals.connect(single_hpsc, single_hpc, {"backends": "config:backends",
                                                  "listen_port": "config:listen_port",
                                                  "protocol": "config:protocol",
                                                  "name": "config:name"})

    for single_hpc, single_hpsc in zip(hpc, hpsc_pb):
        # signals.connect(single_hpsc, single_hpc, {'protocol': 'configs_protocols',
        #                                           'listen_port': 'listen_ports',
        #                                           'name': 'configs_names',
        #                                           'servers': 'configs',
        #                                           'ports': 'configs_ports'})
        signals.connect(single_hpsc, single_hpc, {"backends": "config:backends",
                                                  "listen_port": "config:listen_port",
                                                  "protocol": "config:protocol",
                                                  "name": "config:name"})

    # for single_hps, single_hpc in zip(hps, hpc):
    #     signals.connect(single_hpc, single_hps, {'listen_ports': 'ports'},
    #                     events=False)

    # assign haproxy services to each node

    node1 = resource.load('node1')
    node2 = resource.load('node2')
    node3 = resource.load('node3')
    nodes = [node1, node2, node3]

    for single_node, single_hps in zip(nodes, hps):
        signals.connect(single_node, single_hps)

    for single_node, single_hpc in zip(nodes, hpc):
        signals.connect(single_node, single_hpc)

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
