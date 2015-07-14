


from functools import partial, wraps
from itertools import islice
import subprocess
import time

from celery import Celery
from celery.app import task
from celery import group
from celery.exceptions import Ignore
import redis

from solar.orchestration import graph
from solar.core import actions
from solar.core import resource


app = Celery(
    'tasks',
    backend='redis://10.0.0.2:6379/1',
    broker='redis://10.0.0.2:6379/1')
app.conf.update(CELERY_ACCEPT_CONTENT = ['json'])
app.conf.update(CELERY_TASK_SERIALIZER = 'json')

r = redis.StrictRedis(host='10.0.0.2', port=6379, db=1)


class ReportTask(task.Task):

    def on_success(self, retval, task_id, args, kwargs):
        schedule_next.apply_async(args=[task_id, 'SUCCESS'], queue='scheduler')

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        schedule_next.apply_async(
            args=[task_id, 'ERROR'],
            kwargs={'errmsg': str(einfo.exception)},
            queue='scheduler')


report_task = partial(app.task, base=ReportTask, bind=True)


@report_task
def solar_resource(ctxt, resource_name, action):
    res = resource.load(resource_name)
    return actions.resource_action(res, action)


@report_task
def cmd(ctxt, cmd):
    popen = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = popen.communicate()
    rcode = popen.returncode
    if rcode:
        raise Exception('Command %s failed with err %s', cmd, err)
    return popen.returncode, out, err


@report_task
def sleep(ctxt, seconds):
    time.sleep(seconds)


@report_task
def error(ctxt, message):
    raise Exception('message')


@report_task
def fault_tolerance(ctxt, percent):
    task_id = ctxt.request.id
    plan_uid, task_name = task_id.rsplit(':', 1)

    dg = graph.get_graph(plan_uid)
    success = 0.0
    predecessors = dg.predecessors(task_name)
    lth = len(predecessors)

    for s in predecessors:
        if dg.node[s]['status'] == 'SUCCESS':
            success += 1

    succes_percent = (success/lth) * 100
    if succes_percent < percent:
        raise Exception('Cant proceed with, {0} < {1}'.format(
            succes_percent, percent))


@report_task
def echo(ctxt, message):
    return message


@report_task
def anchor(ctxt, *args):
    # such tasks should be walked when atleast 1/3/exact number of resources visited
    dg = graph.get_graph('current')
    for s in dg.predecessors(ctxt.request.id):
        if dg.node[s]['status'] != 'SUCCESS':
            raise Exception('One of the tasks erred, cant proceeed')


def schedule(plan_uid, dg):
    next_tasks = list(traverse(dg))
    graph.save_graph(plan_uid, dg)
    print 'GRAPH {0}\n NEXT TASKS {1}'.format(dg.node, next_tasks)
    group(next_tasks)()


@app.task
def schedule_start(plan_uid, start=None, end=None):
    """On receive finished task should update storage with task result:

    - find successors that should be executed
    - apply different policies to tasks
    """
    dg = graph.get_graph(plan_uid)
    dg.graph['stop'] = False
    schedule(plan_uid, dg)


@app.task
def schedule_next(task_id, status, errmsg=None):
    plan_uid, task_name = task_id.rsplit(':', 1)
    dg = graph.get_graph(plan_uid)
    dg.node[task_name]['status'] = status
    dg.node[task_name]['errmsg'] = errmsg

    schedule(plan_uid, dg)

# TODO(dshulyak) some tasks should be evaluated even if not all predecessors
# succeded, how to identify this?
# - add ignor_error on edge
# - add ignore_predecessor_errors on task in consideration
# - make fault_tolerance not a task but a policy for all tasks
control_tasks = [fault_tolerance, anchor]


def traverse(dg):
    """
    1. Node should be visited only when all predecessors already visited
    2. Visited nodes should have any state except PENDING, INPROGRESS, for now
    is SUCCESS or ERROR, but it can be extended
    3. If node is INPROGRESS it should not be visited once again
    """
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
            task_id = '{}:{}'.format(dg.graph['uid'], node)

            task_name = '{}.{}'.format(__name__, data['type'])
            task = app.tasks[task_name]

            if all_success(dg, predecessors) or task in control_tasks:
                dg.node[node]['status'] = 'INPROGRESS'
                for t in generate_task(task, dg, data, task_id):
                    yield t


def generate_task(task, dg, data, task_id):

    subtask = task.subtask(
        data['args'], task_id=task_id,
        time_limit=data.get('time_limit', None),
        soft_time_limit=data.get('soft_time_limit', None))

    if data.get('target', None):
        subtask.set(queue=data['target'])

    yield subtask


def all_success(dg, nodes):
    return all((dg.node[n]['status'] == 'SUCCESS' for n in nodes))
