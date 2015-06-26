#!/usr/bin/python


import click

from orch import graph
from orch import tasks


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
        'PENDING': 'white',
        'ERROR': 'red',
        'SUCCESS': 'green',
        'INPROGRESS': 'yellow'}

    report = graph.report_topo(uid)
    for item in report:
        click.echo(
            click.style('{} -> {}'.format(item[0], item[1]), fg=colors[item[1]]))


@click.command()
@click.argument('uid')
@click.option('--start', default=None)
@click.option('--end', default=None)
def execute(uid, start, end):
    tasks.schedule_start.apply_async(
        args=[uid],
        kwargs={'start': start, 'end': end},
        queue='master')


@click.command()
@click.argument('uid')
@click.option('--reset', default=False, is_flag=True)
def restart(uid, reset):
    if reset:
        graph.reset(uid)
    tasks.schedule_start.apply_async(args=[uid], queue='master')


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
    tasks.schedule_start.apply_async(args=[uid], queue='master')


orchestration.add_command(create)
orchestration.add_command(update)
orchestration.add_command(report)
orchestration.add_command(execute)
orchestration.add_command(restart)
orchestration.add_command(reset)
orchestration.add_command(stop)
orchestration.add_command(retry)


if __name__ == '__main__':
    orchestration()
