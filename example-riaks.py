import click
import sys
import time

from solar.core import actions
from solar.core import resource
from solar.core import signals
from solar.core import validation
from solar.core.resource import virtual_resource as vr
from solar import errors

from solar.interfaces.db import get_db

from solar import events as evapi
from solar.events.controls import React, Dep
from solar.events.api import add_event


db = get_db()


def setup_riak():
    db.clear()
    signals.Connections.clear()

    nodes = vr.create('nodes', 'templates/riak_nodes.yml', {})
    node1, node2, node3 = nodes

    riak_services = []
    ips = '10.0.0.%d'
    for i in xrange(3):
        num = i + 1
        ip = ips % (num + 2)  # XXX: da rade inaczej ?
        r = vr.create('riak_service%d' % num,
                      'resources/riak_node',
                      {'riak_name': 'riak%d@%s' % (num, ip)})[0]
        riak_services.append(r)

    for i, riak in enumerate(riak_services):
        signals.connect(nodes[i], riak)

    for i, riak in enumerate(riak_services[1:]):
        signals.connect(riak_services[0], riak, {'riak_name': 'join_to'})

    has_errors = False
    for r in locals().values():

        # TODO: handle list
        if not isinstance(r, resource.Resource):
            continue

        # print 'Validating {}'.format(r.name)
        errors = validation.validate_resource(r)
        if errors:
            has_errors = True
            print 'ERROR: %s: %s' % (r.name, errors)

    if has_errors:
        print "ERRORS"
        sys.exit(1)

    events = [
        Dep('riak_service2', 'run', 'success', 'riak_service3', 'join'),
        Dep('riak_service3', 'run', 'success', 'riak_service2', 'join'),

        React('riak_service1', 'run', 'success', 'riak_service2', 'join'),
        React('riak_service1', 'run', 'success', 'riak_service3', 'join'),

        React('riak_service2', 'run', 'success', 'riak_service2', 'join'),
        React('riak_service3', 'run', 'success', 'riak_service3', 'join'),

        React('riak_service3', 'join', 'success', 'riak_service1', 'commit'),
        React('riak_service2', 'join', 'success', 'riak_service1', 'commit')
    ]

    for event in events:
        add_event(event)

    print 'Use solar changes process & orch'
    sys.exit(1)



@click.group()
def main():
    pass


@click.command()
def deploy():
    setup_riak()


@click.command()
def undeploy():
    raise NotImplemented("Not yet")



main.add_command(deploy)
main.add_command(undeploy)


if __name__ == '__main__':
    main()
