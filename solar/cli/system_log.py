#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import sys

import click

from solar.cli.base import BaseGroup
from solar.cli.uids_history import remember_uid
from solar.core import resource
from solar.core import testing
from solar import errors
from solar.system_log import change
from solar.system_log import data


class SystemLogGroup(BaseGroup):
    pass


@click.group(cls=SystemLogGroup)
def changes():
    pass


@changes.command()
def validate():
    errors = resource.validate_resources()
    if errors:
        for r, error in errors:
            print('ERROR: %s: %s' % (r.name, error))
        sys.exit(1)


@changes.command()
@click.option('--action', '-a', default=None, help='resource action')
@click.option('--name', '-n', default=None, help='resource name')
@click.option('--tag', '-t', multiple=True, help='resource tags')
@click.option('-d', default=False, is_flag=True, help='detailed view')
def stage(action, name, tag, d):
    if action and (name or tag):
        resource.stage_resources(name or tag, action)
    log = change.staged_log(populate_with_changes=True)
    for item in log:
        click.echo(data.compact(item))
        if d:
            for line in data.details(item.diff):
                click.echo(' ' * 4 + line)
    if not log:
        click.echo('No changes')


@changes.command(name='staged-item')
@click.argument('uid')
def staged_item(uid):
    item = data.LogItem.get(uid)
    if not item:
        click.echo('No staged changes for {}'.format(uid))
    else:
        click.echo(data.compact(item))
        for line in data.details(item.diff):
            click.echo(' ' * 4 + line)


@changes.command()
@click.option('--tag', '-t', multiple=True, help='resource tags')
def process(tag):
    uid = change.send_to_orchestration(tag).graph['uid']
    remember_uid(uid)
    click.echo(uid)


@changes.command()
@click.option('-n', default=5, help='number of items to show')
@click.option('-d', default=False, is_flag=True, help='detailed view')
@click.option('-s', default=False, is_flag=True, help='short view, only uid')
def history(n, d, s):
    log = data.CL()
    for item in log:
        if s:
            click.echo(item.uid)
            continue

        click.echo(data.compact(item))
        if d:
            for line in data.details(item.diff):
                click.echo(' ' * 4 + line)
    if not log:
        click.echo('No history')


@changes.command()
@click.argument('uid')
def revert(uid):
    try:
        change.revert(uid)
    except errors.SolarError as er:
        raise click.BadParameter(str(er))


@changes.command()
@click.argument('uids', nargs=-1)
@click.option('--all', is_flag=True, default=True)
def discard(uids, all):
    """uids argument should be of a higher priority than all flag."""
    if uids:
        change.discard_uids(uids)
    elif all:
        change.discard_all()


@changes.command()
@click.option('--name', default=None)
def test(name):
    if name:
        results = testing.test(name)
    else:
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
    change.clear_history()


@changes.command(help='USE ONLY FOR TESTING')
def commit():
    change.commit_all()
