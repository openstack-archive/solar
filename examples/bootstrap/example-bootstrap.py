#!/usr/bin/env python

import click
import sys
import time

from solar.core import actions
from solar.core import resource
from solar.core import signals
from solar.core import validation
from solar.core.resource import composer as cr
from solar import errors
from solar.dblayer.model import ModelMeta


@click.group()
def main():
    pass


def setup_resources():
    ModelMeta.remove_all()

    node2 = cr.create('node2', 'resources/ro_node/', {
        'ip': '10.0.0.4',
        'ssh_key': '/vagrant/.vagrant/machines/solar-dev2/virtualbox/private_key',
        'ssh_user': 'vagrant'
    })[0]

    solar_bootstrap2 = cr.create('solar_bootstrap2', 'resources/solar_bootstrap', {'master_ip': '10.0.0.2'})[0]

    signals.connect(node2, solar_bootstrap2)

    has_errors = False
    for r in locals().values():
        if not isinstance(r, resource.Resource):
            continue

        print 'Validating {}'.format(r.name)
        errors = validation.validate_resource(r)
        if errors:
            has_errors = True
            print 'ERROR: %s: %s' % (r.name, errors)

    if has_errors:
        sys.exit(1)

resources_to_run = [
    'solar_bootstrap2',
]


@click.command()
def deploy():
    setup_resources()

    # run
    resources = resource.load_all()
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
    resources = resource.load_all()
    resources = {r.name: r for r in resources}

    for name in reversed(resources_to_run):
        try:
            actions.resource_action(resources[name], 'remove')
        except errors.SolarError as e:
            print 'WARNING: %s' % str(e)

    ModelMeta.remove_all()

main.add_command(deploy)
main.add_command(undeploy)


if __name__ == '__main__':
    main()
