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

    joiners = []
    for i in xrange(2):
        num = i + 1
        join = vr.create('riak_join_single%d' % num,
                         'resources/riak_join_single', {})[0]
        joiners.append(join)

    for i, riak in enumerate(riak_services[:-1]):
        signals.connect(nodes[i+1], joiners[i])
        signals.connect(riak, joiners[i], {'riak_name': 'join_to'})
        # signals.connect(riak, riak_joiner_service, {'riak_name': 'join_to'})
        # signals.connect(riak, riak_joiner_service, {'ip': 'join_from'})

    commiter = vr.create('riak_commit1', 'resources/riak_commit', {})[0]
    # for joiner in joiners:
    #     signals.connect(joiner, commiter, {'join_to': 'riak_names'})
    signals.connect(node1, commiter)

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
        React('riak_service2', 'run', 'success', 'riak_join_single1', 'join'),
        React('riak_service3', 'run', 'success', 'riak_join_single2', 'join'),
        React('riak_join_single1', 'join', 'success', 'riak_commit1', 'commit'),
        React('riak_join_single2', 'join', 'success', 'riak_commit1', 'commit')
    ]

    for event in events:
        add_event(event)

    print 'Use orch'
    sys.exit(1)


resources_to_run = [
    'riak_service1',
    'riak_service2',
    'riak_service3',
    # 'riak_join_single1',
    # 'riak_join_single2',
    # 'riak_commit1'
]



@click.group()
def main():
    pass


@click.command()
def deploy():
    setup_riak()

    resources = map(resource.wrap_resource, db.get_list(collection=db.COLLECTIONS.resource))
    resources = {r.name: r for r in resources}

    for name in resources_to_run:
        try:
            actions.resource_action(resources[name], 'run')
        except errors.SolarError as e:
            print 'WARNING: %s' % str(e)
            raise

    time.sleep(10)


@click.command()
def undeploy():
    resources = map(resource.wrap_resource, db.get_list(collection=db.COLLECTIONS.resource))
    resources = {r.name: r for r in resources}

    for name in reversed(resources_to_run):
        try:
            actions.resource_action(resources[name], 'remove')
        except errors.SolarError as e:
            print 'WARNING: %s' % str(e)

    db.clear()

    signals.Connections.clear()



main.add_command(deploy)
main.add_command(undeploy)


if __name__ == '__main__':
    main()
