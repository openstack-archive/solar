#!/usr/bin/python

import click

from solar.orchestration import graph
from solar.orchestration import tasks
from solar.orchestration import filters
from solar.orchestration import utils
from solar.cli.uids_history import SOLARUID


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
@click.argument('plan', type=click.File('rb'))
def create(plan):
    click.echo(graph.create_plan(plan.read()).graph['uid'])


@orchestration.command()
@click.argument('uid', type=SOLARUID)
@click.argument('plan', type=click.File('rb'))
def update(uid, plan):
    graph.update_plan(uid, plan.read())


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
        click.echo(click.style(msg, fg=colors[item[1]]))

@orchestration.command()
@click.argument('uid', type=SOLARUID)
@click.option('--start', '-s', multiple=True)
@click.option('--end', '-e', multiple=True)
def filter(uid, start, end):
    graph.reset_filtered(uid)
    plan = filters.filter(
        graph.get_graph(uid), start=start, end=end)
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
        plan = filters.filter(plan, start=start, end=end)
    utils.write_graph(plan)
    click.echo('Created {name}.png'.format(name=plan.graph['name']))


@orchestration.command()
@click.argument('uid', type=SOLARUID)
def show(uid):
    click.echo(graph.show(uid))
