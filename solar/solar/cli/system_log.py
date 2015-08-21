
import sys

import click

from solar.core import testing
from solar.core import resource
from solar.system_log import change
from solar.system_log import operations
from solar.system_log import data
from solar.cli.uids_history import get_uid, remember_uid, SOLARUID


@click.group()
def changes():
    pass


@changes.command()
def validate():
    errors = resource.validate_resources()
    if errors:
        for r, error in errors:
            print 'ERROR: %s: %s' % (r.name, error)
        sys.exit(1)


@changes.command()
def stage():
    log = change.stage_changes()
    staged = list(log.reverse())
    if not staged:
        click.echo('No changes')
    click.echo(staged)


@changes.command()
def process():
    uid = change.send_to_orchestration()
    remember_uid(uid)
    click.echo(uid)


@changes.command()
@click.argument('uid', type=SOLARUID)
def commit(uid):
    operations.commit(uid)


@changes.command()
@click.option('-n', default=5)
def history(n):
    commited = list(data.CL().collection(n))
    if not commited:
        click.echo('No history.')
        return
    commited.reverse()
    click.echo(commited)


@changes.command()
def test():
    testing.test_all()


@changes.command(name='clean-history')
def clean_history():
    data.CL().clean()
    data.CD().clean()
