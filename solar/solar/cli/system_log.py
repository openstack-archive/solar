
import sys

import click

from solar.core import testing
from solar.core import virtual_resource as vr
from solar.system_log import change
from solar.system_log import operations
from solar.system_log import data


@click.group()
def changes():
    pass


@changes.command()
def validate():
    errors = vr.validate_resources()
    if errors:
        for r, error in errors:
            print 'ERROR: %s: %s' % (r.name, error)
        sys.exit(1)


@changes.command()
def stage():
    log = change.stage_changes()
    click.echo(list(log.collection()))


@changes.command()
def send():
    click.echo(change.send_to_orchestration())


@changes.command()
@click.argument('uid')
def commit(uid):
    operations.commit(uid)


@changes.command()
@click.option('-n', default=5)
def history(n):
    click.echo(list(data.CL().collection(n)))


@changes.command()
def test():
    testing.test_all()
