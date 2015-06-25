
from celery import Celery
from celery.app import task
from celery import group
from celery.exceptions import Ignore

from functools import partial, wraps
from itertools import islice

import subprocess
import time

from orch import graph

import redis

app = Celery(
    'tasks',
    backend='redis://10.0.0.2:6379/1',
    broker='redis://10.0.0.2:6379/1')

r = redis.StrictRedis(host='10.0.0.2', port=6379, db=1)


class ReportTask(task.Task):

    def on_success(self, retval, task_id, args, kwargs):
        schedule_next.apply_async(args=[task_id, 'SUCCESS'], queue='master')

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        schedule_next.apply_async(args=[task_id, 'ERROR'], queue='master')


solar_task = partial(app.task, base=ReportTask, bind=True)


def maybe_ignore(func):
    """used to ignore tasks when they are in queue, but should be discarded
    """

    @wraps(func)
    def wrapper(ctxt, *args, **kwargs):
        if r.sismember('tasks.ignore', ctxt.request.id):
            raise Ignore()
        return func(ctxt, *args, **kwargs)
    return wrapper


@solar_task
@maybe_ignore
def cmd(cmd):
    popen = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = popen.communicate()
    rcode = popen.returncode
    if rcode:
        raise Exception('Command %s failed with err %s', cmd, err)
    return popen.returncode, out, err


@solar_task
@maybe_ignore
def sleep(ctxt, seconds):
    time.sleep(seconds)


@solar_task
@maybe_ignore
def error(ctxt, message):
    raise Exception('message')


@solar_task
def fault_tolerance(ctxt, percent):
    dg = graph.get_graph('current')
    success = 0.0
    predecessors = dg.predecessors(ctxt.request.id)
    lth = len(predecessors)

    for s in predecessors:
        if dg.node[s]['status'] == 'SUCCESS':
            success += 1

    succes_percent = (success/lth) * 100
    if succes_percent < percent:
        raise Exception('Cant proceed with, {0} < {1}'.format(
            succes_percent, percent))


@solar_task
@maybe_ignore
def echo(ctxt, message):
    return message


@solar_task
def anchor(ctxt, *args):
    # it should be configurable to wait for atleast 1 / 3 resources
    dg = graph.get_graph('current')
    for s in dg.predecessors(ctxt.request.id):
        if dg.node[s]['status'] != 'SUCCESS':
            raise Exception('One of the tasks erred, cant proceeed')


@app.task
def fire_timeout(task_id):
    result = app.AsyncResult(task_id)
    if result.state in ['ERROR', 'SUCCESS']:
        return
    r.sadd('tasks.ignore', task_id)
    schedule_next.apply_async(args=[task_id, 'ERROR'], queue='master')


@app.task
def schedule_start():
    """On receive finished task should update storage with task result:

    - find successors that should be executed
    - apply different policies to tasks
    """
    dg = graph.get_graph('current')

    concurrency = dg.graph.get('concurrency', None)
    next_tasks = list(islice(get_next(dg), 0, concurrency))
    print 'GRAPH {0}\n NEXT TASKS {1}'.format(dg.node, next_tasks)
    graph.save_graph('current', dg)
    group(next_tasks)()


@app.task
def schedule_next(task_id, status):
    dg = graph.get_graph('current')
    dg.node[task_id]['status'] = status
    concurrency = dg.graph.get('concurrency', None)
    next_tasks = list(islice(get_next(dg), 0, concurrency))
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
            subtask = task.subtask(
                data['args'], task_id=node,
                time_limit=data.get('time_limit', None),
                soft_time_limit=data.get('soft_time_limit', None))

            if data.get('target', None):
                subtask.set(queue=data['target'])

            timeout = data.get('timeout')

            yield subtask

            if timeout:
                timeout_task = fire_timeout.subtask([node], countdown=timeout)
                timeout_task.set(queue='master')
                yield timeout_task

