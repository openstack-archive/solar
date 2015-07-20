#!/usr/bin/python

import subprocess

import click
import networkx as nx

from solar.orchestration import graph
from solar.orchestration import tasks


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
    click.echo(graph.create_plan(plan.read()))


@orchestration.command()
@click.argument('uid')
@click.argument('plan', type=click.File('rb'))
def update(uid, plan):
    graph.update_plan(uid, plan.read())


@orchestration.command()
@click.argument('uid')
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

@orchestration.command(name='run-once')
@click.argument('uid')
@click.option('--start', default=None)
@click.option('--end', default=None)
def run_once(uid, start, end):
    tasks.schedule_start.apply_async(
        args=[uid],
        kwargs={'start': start, 'end': end},
        queue='scheduler')

@orchestration.command()
@click.argument('uid')
def restart(uid):
    graph.reset(uid)
    tasks.schedule_start.apply_async(args=[uid], queue='scheduler')


@orchestration.command()
@click.argument('uid')
def reset(uid):
    graph.reset(uid)


@orchestration.command()
@click.argument('uid')
def stop(uid):
    # TODO(dshulyak) how to do "hard" stop?
    # using revoke(terminate=True) will lead to inability to restart execution
    # research possibility of customizations of
    # app.control and Panel.register in celery
    tasks.soft_stop.apply_async(args=[uid], queue='scheduler')


@orchestration.command()
@click.argument('uid')
def resume(uid):
    graph.reset(uid, ['SKIPPED'])
    tasks.schedule_start.apply_async(args=[uid], queue='scheduler')


@orchestration.command()
@click.argument('uid')
def retry(uid):
    graph.reset(uid, ['ERROR'])
    tasks.schedule_start.apply_async(args=[uid], queue='scheduler')


@orchestration.command()
@click.argument('uid')
def dg(uid):
    plan = graph.get_graph(uid)

    colors = {
        'PENDING': 'cyan',
        'ERROR': 'red',
        'SUCCESS': 'green',
        'INPROGRESS': 'yellow',
        'SKIPPED': 'blue'}

    for n in plan:
        color = colors[plan.node[n]['status']]
        plan.node[n]['color'] = color
    nx.write_dot(plan, '{name}.dot'.format(name=plan.graph['name']))
    subprocess.call(
        'tred {name}.dot | dot -Tpng -o {name}.png'.format(name=plan.graph['name']),
        shell=True)
    click.echo('Created {name}.png'.format(name=plan.graph['name']))


@orchestration.command()
@click.argument('uid')
def show(uid):
    click.echo(graph.show(uid))
