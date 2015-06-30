#!/usr/bin/python


import click

from orch import graph
from orch import tasks

import networkx as nx
import subprocess

@click.group()
def orchestration():
    """
    \b
    ./cli.py create orch/examples/multi.yaml
    <id>
    ./cli.py execute <id>
    ./cli.py report <id>
    <task> -> <status>
    ./cli.py restart <id> --reset
    """


@click.command()
@click.argument('plan', type=click.File('rb'))
def create(plan):
    click.echo(graph.create_plan(plan.read()))


@click.command()
@click.argument('uid')
@click.argument('plan', type=click.File('rb'))
def update(uid, plan):
    graph.update_plan(uid, plan.read())

@click.command()
@click.argument('uid')
def report(uid):
    colors = {
        'PENDING': 'blue',
        'ERROR': 'red',
        'SUCCESS': 'green',
        'INPROGRESS': 'yellow'}

    report = graph.report_topo(uid)
    for item in report:
        msg = '{} -> {}'.format(item[0], item[1])
        if item[2]:
            msg += ' :: {}'.format(item[2])
        click.echo(click.style(msg, fg=colors[item[1]]))


@click.command()
@click.argument('uid')
@click.option('--start', default=None)
@click.option('--end', default=None)
def execute(uid, start, end):
    tasks.schedule_start.apply_async(
        args=[uid],
        kwargs={'start': start, 'end': end},
        queue='scheduler')


@click.command()
@click.argument('uid')
def restart(uid):
    graph.reset(uid)
    tasks.schedule_start.apply_async(args=[uid], queue='scheduler')


@click.command()
@click.argument('uid')
def reset(uid):
    graph.reset(uid)


@click.command()
@click.argument('uid')
def stop(uid):
    # TODO(dshulyak) how to do "hard" stop?
    # using revoke(terminate=True) will lead to inability to restart execution
    # research possibility of customizations of
    # app.control and Panel.register in celery
    graph.soft_stop(uid)


@click.command()
@click.argument('uid')
def retry(uid):
    graph.reset(uid, ['ERROR'])
    tasks.schedule_start.apply_async(args=[uid], queue='scheduler')


@click.command()
@click.argument('uid')
def dg(uid):
    plan = graph.get_graph(uid)

    colors = {
        'PENDING': 'blue',
        'ERROR': 'red',
        'SUCCESS': 'green',
        'INPROGRESS': 'yellow'}

    for n in plan:
        color = colors[plan.node[n]['status']]
        plan.node[n]['color'] = color
    nx.write_dot(plan, 'graph.dot')
    subprocess.call(['dot', '-Tpng', 'graph.dot', '-o', 'graph.png'])


orchestration.add_command(create)
orchestration.add_command(update)
orchestration.add_command(report)
orchestration.add_command(execute)
orchestration.add_command(restart)
orchestration.add_command(reset)
orchestration.add_command(stop)
orchestration.add_command(retry)
orchestration.add_command(dg)


if __name__ == '__main__':
    orchestration()
