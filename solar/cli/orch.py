#!/usr/bin/python
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
import time

import click

from solar.cli.base import BaseGroup
from solar.cli.uids_history import remember_uid
from solar.cli.uids_history import SOLARUID
from solar.dblayer.locking import DBLock
from solar import errors
from solar.orchestration import filters
from solar.orchestration import graph
from solar.orchestration import SCHEDULER_CLIENT
from solar.orchestration.traversal import states
from solar.orchestration import utils


class OrchGroup(BaseGroup):
    pass


@click.group(name='orch', cls=OrchGroup)
def orchestration():
    pass


@orchestration.command()
@click.argument('plan')
def create(plan):
    uid = graph.create_plan(plan).graph['uid']
    remember_uid(uid)
    click.echo(uid)


def wait_report(uid, timeout, stop_on_error=False, interval=3):
    try:
        if timeout:
            initial_error_count = None
            for summary in graph.wait_finish(uid, timeout=timeout):
                stringified_summary = '\r' + ' '.join(
                    ['{}: {}'.format(state, count)
                        for state, count in summary.items()])
                click.echo(stringified_summary, nl=False)
                sys.stdout.flush()

                error = states.ERROR.name
                if initial_error_count is None:
                    initial_error_count = summary[error]
                if initial_error_count < summary[error] and stop_on_error:
                    raise errors.SolarError('Error encountered. Stopping')

                pending = states.PENDING.name
                in_progress = states.INPROGRESS.name
                if summary[pending] + summary[in_progress] != 0:
                    time.sleep(interval)
    except errors.SolarError:
        click.echo('')
        click_report(uid)
        raise
    else:
        click.echo('')
        click_report(uid)


def click_report(uid):
    report = graph.report_progress(uid)
    if len(report['tasks']) == 0:
        click.echo('Nothing to report')
    else:
        colors = {
            'PENDING': 'cyan',
            'ERROR': 'red',
            'SUCCESS': 'green',
            'INPROGRESS': 'yellow',
            'SKIPPED': 'blue',
            'NOOP': 'black'}

        for item in report['tasks']:
            msg = '{} -> {}'.format(item[0], item[1])
            if item[2]:
                msg += ' :: {}'.format(item[2])
            click.echo(click.style(msg, fg=colors[item[1]]))
        click.echo('Total Delta: {}'.format(report['total_delta']))
        click.echo('Total Time: {}'.format(report['total_time']))


@orchestration.command()
@click.argument('uid', type=SOLARUID, default='last')
@click.option('-w', 'wait', default=0)
@click.option('-s', '--stop-on-error', is_flag=True, default=False)
def report(uid, wait, stop_on_error):
    wait_report(uid, wait, stop_on_error)


@orchestration.command()
@click.argument('uid', type=SOLARUID)
@click.option('--start', '-s', multiple=True)
@click.option('--end', '-e', multiple=True)
def filter(uid, start, end):
    graph.reset_filtered(uid)
    plan = graph.get_graph(uid)
    errors = filters.filter(plan, start=start, end=end)
    if errors:
        raise click.ClickException('\n'.join(errors))
    graph.update_graph(plan)
    utils.write_graph(plan)
    click.echo('Created {name}.png'.format(name=plan.graph['name']))


@orchestration.command(help='Used to mark task as executed')
@click.argument('uid', type=SOLARUID)
@click.option('--task', '-t', multiple=True)
def noop(uid, task):
    graph.set_states(uid, task)


@orchestration.command(name='run-once')
@click.argument('uid', type=SOLARUID, default='last')
@click.option('-w', 'wait', default=0)
@click.option('-s', '--stop-on-error', is_flag=True, default=False)
def run_once(uid, wait, stop_on_error):
    SCHEDULER_CLIENT.next({}, uid)
    wait_report(uid, wait, stop_on_error)


@orchestration.command()
@click.argument('uid', type=SOLARUID)
@click.option('-w', 'wait', default=0)
@click.option('-s', '--stop-on-error', is_flag=True, default=False)
def restart(uid, wait, stop_on_error):
    graph.reset_by_uid(uid)
    SCHEDULER_CLIENT.next({}, uid)
    wait_report(uid, wait, stop_on_error)


@orchestration.command()
@click.argument('uid', type=SOLARUID)
def stop(uid):
    # TODO(dshulyak) how to do "hard" stop?
    # using revoke(terminate=True) will lead to inability to restart execution
    # research possibility of customizations
    # app.control and Panel.register in celery
    SCHEDULER_CLIENT.soft_stop({}, uid)


@orchestration.command()
@click.argument('uid', type=SOLARUID)
def reset(uid):
    graph.reset_by_uid(uid)


@orchestration.command()
@click.argument('uid', type=SOLARUID)
def resume(uid):
    graph.reset_by_uid(uid, state_list=['SKIPPED'])
    SCHEDULER_CLIENT.next({}, uid)


@orchestration.command()
@click.argument('uid', type=SOLARUID)
def retry(uid):
    graph.reset_by_uid(uid, state_list=['ERROR'])
    SCHEDULER_CLIENT.next({}, uid)


@orchestration.command()
@click.argument('uid', type=SOLARUID)
@click.option('--start', '-s', multiple=True)
@click.option('--end', '-e', multiple=True)
def dg(uid, start, end):
    plan = graph.get_graph(uid)
    if start or end:
        errors = filters.filter(plan, start=start, end=end)
        if errors:
            raise click.ClickException('\n'.join(errors))
    utils.write_graph(plan)
    click.echo('Created {name}.svg'.format(name=plan.graph['name']))


@orchestration.command()
@click.argument('uid', type=SOLARUID)
def show(uid):
    click.echo(graph.show(uid))


@orchestration.command(name='release-lock')
@click.argument('uid', type=SOLARUID)
def release_lock(uid):
    """Use if worker was killed, and lock wasnt released properly. """
    lock = DBLock.get(uid)
    lock.delete()
    return True
