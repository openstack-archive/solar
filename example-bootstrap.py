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


GIT_PUPPET_LIBS_URL = 'https://github.com/CGenie/puppet-libs-resource'


# TODO
# Resource for repository OR puppet apt-module in run.pp
# add-apt-repository cloud-archive:juno
# To discuss: install stuff in Docker container

# NOTE
# No copy of manifests, pull from upstream (implemented in the puppet handler)
# Official puppet manifests, not fuel-library


db = get_db()


@click.group()
def main():
    pass


def setup_resources():
    db.clear()

    signals.Connections.clear()

    node3 = vr.create('node3', 'resources/ro_node/', {
        'ip': '10.0.0.5',
        'ssh_key': '/vagrant/.vagrant/machines/solar-dev3/virtualbox/private_key',
        'ssh_user': 'vagrant'
    })[0]

    solar_bootstrap3 = vr.create('solar_bootstrap3', 'resources/solar_bootstrap', {'master_ip': '10.0.0.2'})[0]

    signals.connect(node3, solar_bootstrap3)

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
    'solar_bootstrap3',
]


@click.command()
def deploy():
    setup_resources()

    # run
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
