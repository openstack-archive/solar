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

from solar.cli.uids_history import remember_uid
from solar.cli.uids_history import SOLARUID
from solar import errors
from solar.orchestration import filters
from solar.orchestration import graph
from solar.orchestration import tasks
from solar.orchestration.traversal import states
from solar.orchestration import utils


@click.group(name='orch')
def orchestration():
    """\b

    create solar/orchestration/examples/multi.yaml
    <id>
    run-once <id>
    report <id>
    <task> -> <status>
    restart <id> --reset
    """


@orchestration.command()
@click.argument('plan')
def create(plan):
    uid = graph.create_plan(plan).graph['uid']
    remember_uid(uid)
    click.echo(uid)


def wait_report(uid, timeout, interval=3):
    try:
        if timeout:
            for summary in graph.wait_finish(uid, timeout=timeout):
                stringified_summary = '\r' + ' '.join(
                    ['{}: {}'.format(state, count)
                        for state, count in summary.items()])
                click.echo(stringified_summary, nl=False)
                sys.stdout.flush()
                pending = states.PENDING.name
                in_progress = states.INPROGRESS.name
                if summary[pending] + summary[in_progress] != 0:
                    time.sleep(interval)
    except errors.SolarError:
        click.echo('')
        click_report(uid)
        sys.exit(1)
    else:
        click.echo('')
        click_report(uid)


def click_report(uid):
    colors = {
        'PENDING': 'cyan',
        'ERROR': 'red',
        'SUCCESS': 'green',
        'INPROGRESS': 'yellow',
        'SKIPPED': 'blue',
        'NOOP': 'black'}

    total = 0.0
    report = graph.report_topo(uid)
    for item in report:
        msg = '{} -> {}'.format(item[0], item[1])
        if item[2]:
            msg += ' :: {}'.format(item[2])
        if item[4] and item[3]:
            delta = float(item[4]) - float(item[3])
            total += delta
            msg += ' D: {}'.format(delta)
        click.echo(click.style(msg, fg=colors[item[1]]))
    click.echo('Delta SUM: {}'.format(total))


@orchestration.command()
@click.argument('uid', type=SOLARUID, default='last')
@click.option('-w', 'wait', default=0)
def report(uid, wait):
    wait_report(uid, wait)


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
def run_once(uid, wait):
    tasks.schedule_start.apply_async(
        args=[uid],
        queue='scheduler')
    wait_report(uid, wait)


@orchestration.command()
@click.argument('uid', type=SOLARUID)
@click.option('-w', 'wait', default=0)
def restart(uid, wait):
    graph.reset_by_uid(uid)
    tasks.schedule_start.apply_async(args=[uid], queue='scheduler')
    wait_report(uid, wait)


@orchestration.command()
@click.argument('uid', type=SOLARUID)
def stop(uid):
    # TODO(dshulyak) how to do "hard" stop?
    # using revoke(terminate=True) will lead to inability to restart execution
    # research possibility of customizations
    # app.control and Panel.register in celery
    tasks.soft_stop.apply_async(args=[uid], queue='scheduler')


@orchestration.command()
@click.argument('uid', type=SOLARUID)
def reset(uid):
    graph.reset_by_uid(uid)


@orchestration.command()
@click.argument('uid', type=SOLARUID)
def resume(uid):
    graph.reset_by_uid(uid, state_list=['SKIPPED'])
    tasks.schedule_start.apply_async(args=[uid], queue='scheduler')


@orchestration.command()
@click.argument('uid', type=SOLARUID)
def retry(uid):
    graph.reset_by_uid(uid, state_list=['ERROR'])
    tasks.schedule_start.apply_async(args=[uid], queue='scheduler')


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
