
from celery import Celery
from celery.app import task
from celery import group

from functools import partial

import subprocess
import time

from orch import graph


app = Celery(
    'tasks',
    backend='redis://10.0.0.2:6379/1',
    broker='redis://10.0.0.2:6379/1')


class ReportTask(task.Task):

    def on_success(self, retval, task_id, args, kwargs):
        schedule_next.apply_async(args=[task_id, 'SUCCESS'], queue='master')

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        schedule_next.apply_async(args=[task_id, 'ERROR'], queue='master')


solar_task = partial(app.task, base=ReportTask)


@solar_task
def cmd(cmd):
    popen = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = popen.communicate()
    return popen.returncode, out, err


@solar_task
def sleep(seconds):
    time.sleep(seconds)


@solar_task
def error(message):
    raise Exception('message')


@solar_task(bind=True)
def fault_tolerance(ctxt, percent):
    dg = graph.get_graph('current')
    success = 0.0
    predecessors = dg.predecessors(ctxt.request.id)
    lth = len(predecessors)

    for s in predecessors:
        if dg.node[s]['status'] == ['SUCCESS']:
            success += 1

    succes_percent = (success/lth) * 100
    if succes_percent < percent:
        raise Exception('Cant proceed with, {0} < {1}'.format(
            succes_percent, percent))


@solar_task
def echo(message):
    return message


@solar_task(bind=True)
def anchor(ctxt, *args):
    dg = graph.get_graph('current')
    for s in dg.predecessors(ctxt.request.id):
        if dg.node[s]['status'] != 'SUCCESS':
            raise Exception('One of the tasks erred, cant proceeed')


@app.task
def schedule_start():
    """On receive finished task should update storage with task result:

    - find successors that should be executed
    - apply different policies to tasks
    """
    dg = graph.get_graph('current')

    next_tasks = list(get_next(dg))
    print 'GRAPH {0}\n NEXT TASKS {1}'.format(dg.node, next_tasks)
    graph.save_graph('current', dg)
    group(next_tasks)()


@app.task
def schedule_next(task_id, status):
    dg = graph.get_graph('current')
    dg.node[task_id]['status'] = status

    next_tasks = list(get_next(dg))
    print 'GRAPH {0}\n NEXT TASKS {1}'.format(dg.node, next_tasks)
    graph.save_graph('current', dg)
    group(next_tasks)()


def get_next(dg):
    visited = set()
    for node in dg:
        data = dg.node[node]
        if data['status'] not in ('PENDING', 'INPROGRESS'):
            visited.add(node)

    for node in dg:
        data = dg.node[node]

        if node in visited:
            continue
        elif data['status'] == 'INPROGRESS':
            continue


        predecessors = set(dg.predecessors(node))

        if predecessors <= visited:

            task_name = 'orch.tasks.{0}'.format(data['type'])
            task = app.tasks[task_name]
            dg.node[node]['status'] = 'INPROGRESS'
            yield task.subtask(data['args'], task_id=node)
