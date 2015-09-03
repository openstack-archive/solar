
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
@click.option('-d', default=False, is_flag=True)
def stage(d):
    log = list(change.stage_changes().reverse())
    for item in log:
        click.echo(item)
        if d:
            for line in item.details:
                click.echo(' '*4+line)
    if not log:
        click.echo('No changes')

@changes.command(name='staged-item')
@click.argument('log_action')
def staged_item(log_action):
    item = data.SL().get(log_action)
    if not item:
        click.echo('No staged changes for {}'.format(log_action))
    else:
        click.echo(item)
        for line in item.details:
            click.echo(' '*4+line)

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
    results = testing.test_all()

    for name, result in results.items():
        msg = '[{status}] {name} {message}'
        kwargs = {
            'name': name,
            'message': '',
            'status': 'OK',
        }

        if result['status'] == 'ok':
            kwargs['status'] = click.style('OK', fg='green')
        else:
            kwargs['status'] = click.style('ERROR', fg='red')
            kwargs['message'] = result['message']

        click.echo(msg.format(**kwargs))


@changes.command(name='clean-history')
def clean_history():
    data.CL().clean()
    data.CD().clean()
