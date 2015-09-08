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

import click

from solar.orchestration import graph
from solar.orchestration import tasks
from solar.orchestration import filters
from solar.orchestration import utils
from solar.cli.uids_history import SOLARUID, remember_uid


@click.group(name='orch')
def orchestration():
    """
    \b
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


@orchestration.command()
@click.argument('uid', type=SOLARUID)
@click.argument('plan')
def update(uid, plan):
    graph.update_plan(uid, plan)


@orchestration.command()
@click.argument('uid', type=SOLARUID)
def report(uid):
    colors = {
        'PENDING': 'cyan',
        'ERROR': 'red',
        'SUCCESS': 'green',
        'INPROGRESS': 'yellow',
        'SKIPPED': 'blue'}

    report = graph.report_topo(uid)
    for item in report:
        msg = '{} -> {}'.format(item[0], item[1])
        if item[2]:
            msg += ' :: {}'.format(item[2])
        msg += ' S: {} E: {}'.format(item[3], item[4])
        click.echo(click.style(msg, fg=colors[item[1]]))

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
    graph.save_graph(uid, plan)
    utils.write_graph(plan)
    click.echo('Created {name}.png'.format(name=plan.graph['name']))


@orchestration.command(name='run-once')
@click.argument('uid', type=SOLARUID)
def run_once(uid):
    tasks.schedule_start.apply_async(
        args=[uid],
        queue='scheduler')


@orchestration.command()
@click.argument('uid', type=SOLARUID)
def restart(uid):
    graph.reset(uid)
    tasks.schedule_start.apply_async(args=[uid], queue='scheduler')


@orchestration.command()
@click.argument('uid', type=SOLARUID)
def reset(uid):
    graph.reset(uid)


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
def resume(uid):
    graph.reset(uid, ['SKIPPED'])
    tasks.schedule_start.apply_async(args=[uid], queue='scheduler')


@orchestration.command()
@click.argument('uid', type=SOLARUID)
def retry(uid):
    graph.reset(uid, ['ERROR'])
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
    click.echo('Created {name}.png'.format(name=plan.graph['name']))


@orchestration.command()
@click.argument('uid', type=SOLARUID)
def show(uid):
    click.echo(graph.show(uid))
