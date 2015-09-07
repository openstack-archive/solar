#!/usr/bin/env python

"""
To run this code, first compile the resources with

solar resource compile_all

NOTE: this script might be outdated, the idea is just to show how
      compiled resources work.
"""

import click
import json
import requests
import sys
import time

from solar.core import actions
from solar.core.resource import virtual_resource as vr
from solar.core import resource
from solar.core import signals

from solar.interfaces.db import get_db
from solar.core.resource_provider import  GitProvider, RemoteZipProvider


import resources_compiled


@click.group()
def main():
    pass


@click.command()
def deploy():
    db = get_db()
    db.clear()

    signals.Connections.clear()

    node1 = resources_compiled.RoNodeResource('node1', None, {})
    node1.ip = '10.0.0.3'
    node1.ssh_key = '/vagrant/.vagrant/machines/solar-dev1/virtualbox/private_key'
    node1.ssh_user = 'vagrant'

    rabbitmq_service1 = resources_compiled.RabbitmqServiceResource('rabbitmq_service1', None, {'management_port': 15672, 'port': 5672, 'container_name': 'rabbitmq_service1', 'image': 'rabbitmq:3-management'})
    openstack_vhost = resource.create('openstack_vhost', 'resources/rabbitmq_vhost/', {'vhost_name': 'openstack'})[0]
    openstack_rabbitmq_user = resource.create('openstack_rabbitmq_user', 'resources/rabbitmq_user/', {'user_name': 'openstack', 'password': 'openstack_password'})[0]

    ####
    # connections
    ####

    # rabbitmq
    signals.connect(node1, rabbitmq_service1)
    signals.connect(rabbitmq_service1, openstack_vhost)
    signals.connect(rabbitmq_service1, openstack_rabbitmq_user)
    signals.connect(openstack_vhost, openstack_rabbitmq_user, {'vhost_name': 'vhost_name'})


    errors = vr.validate_resources()
    if errors:
        for r, error in errors:
            print 'ERROR: %s: %s' % (r.name, error)
        sys.exit(1)


    # run
    actions.resource_action(rabbitmq_service1, 'run')
    actions.resource_action(openstack_vhost, 'run')
    actions.resource_action(openstack_rabbitmq_user, 'run')
    time.sleep(10)


@click.command()
def undeploy():
    db = get_db()

    resources = map(resource.wrap_resource, db.get_list(collection=db.COLLECTIONS.resource))
    resources = {r.name: r for r in resources}

    actions.resource_action(resources['openstack_rabbitmq_user'], 'remove')
    actions.resource_action(resources['openstack_vhost'], 'remove')
    actions.resource_action(resources['rabbitmq_service1'], 'remove')

    db.clear()

    signals.Connections.clear()


main.add_command(deploy)
main.add_command(undeploy)


if __name__ == '__main__':
    main()
