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

import subprocess
import time

from functools import partial

from celery.app import task
from celery.signals import task_postrun
from celery.signals import task_prerun

from solar.core import actions
from solar.core.log import log
from solar.core import resource
from solar.dblayer import ModelMeta
from solar.orchestration import executor
from solar.orchestration import graph
from solar.orchestration import limits
from solar.orchestration.runner import app
from solar.orchestration.traversal import traverse
from solar.system_log.tasks import commit_logitem
from solar.system_log.tasks import error_logitem

from solar.dblayer.locking import Lock
from solar.utils import get_current_ident


__all__ = ['solar_resource', 'cmd', 'sleep',
           'error', 'fault_tolerance', 'schedule_start', 'schedule_next']


# NOTE(dshulyak) i am not using celery.signals because it is not possible
# to extract task_id from *task_success* signal
class ReportTask(task.Task):

    def on_success(self, retval, task_id, args, kwargs):
        schedule_next.apply_async(
            args=[task_id, 'SUCCESS'],
            queue='scheduler')
        commit_logitem.apply_async(args=[task_id], queue='system_log')

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        schedule_next.apply_async(
            args=[task_id, 'ERROR'],
            kwargs={'errmsg': str(einfo.exception)},
            queue='scheduler')
        error_logitem.apply_async(args=[task_id], queue='system_log')


report_task = partial(app.task, base=ReportTask, bind=True)


@task_prerun.connect
def start_solar_session(task_id, task, *args, **kwargs):
    ModelMeta.session_start()


@task_postrun.connect
def end_solar_session(task_id, task, *args, **kwargs):
    ModelMeta.session_end()


@report_task(name='solar_resource')
def solar_resource(ctxt, resource_name, action):
    log.debug('TASK solar resource NAME %s ACTION %s',
              resource_name, action)
    res = resource.load(resource_name)
    return actions.resource_action(res, action)


@report_task(name='cmd')
def cmd(ctxt, cmd):
    popen = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = popen.communicate()
    rcode = popen.returncode
    if rcode:
        raise Exception('Command %s failed with err %s', cmd, err)
    return popen.returncode, out, err


@report_task(name='sleep')
def sleep(ctxt, seconds):
    time.sleep(seconds)


@report_task(name='error')
def error(ctxt, message):
    raise Exception('message')


@report_task(name='fault_tolerance')
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

    succes_percent = (success / lth) * 100
    if succes_percent < percent:
        raise Exception('Cant proceed with, {0} < {1}'.format(
            succes_percent, percent))


@report_task(name='echo')
def echo(ctxt, message):
    return message


@report_task(name='anchor')
def anchor(ctxt, *args):
    # such tasks should be walked when atleast 1/3/exact number of resources
    # visited
    dg = graph.get_graph('current')
    for s in dg.predecessors(ctxt.request.id):
        if dg.node[s]['status'] != 'SUCCESS':
            raise Exception('One of the tasks erred, cant proceeed')


def schedule(plan_uid, dg):
    tasks = traverse(dg)
    filtered_tasks = list(limits.get_default_chain(
        dg,
        [t for t in dg if dg.node[t]['status'] == 'INPROGRESS'],
        tasks))
    log.debug('Schedule next tasks %r', filtered_tasks)
    execution = executor.celery_executor(
        dg, filtered_tasks, control_tasks=('fault_tolerance',))
    graph.update_graph(dg)
    execution()


@app.task(name='schedule_start')
def schedule_start(plan_uid):
    """On receive finished task should update storage with task result:

    - find successors that should be executed
    - apply different policies to tasks
    """
    with Lock(plan_uid, str(get_current_ident()), retries=20, wait=1):
        dg = graph.get_graph(plan_uid)
        schedule(plan_uid, dg)


@app.task(name='soft_stop')
def soft_stop(plan_uid):
    with Lock(plan_uid, str(get_current_ident()), retries=20, wait=1):
        dg = graph.get_graph(plan_uid)
        for n in dg:
            if dg.node[n]['status'] == 'PENDING':
                dg.node[n]['status'] = 'SKIPPED'
        graph.update_graph(dg)


@app.task(name='schedule_next')
def schedule_next(task_id, status, errmsg=None):
    plan_uid, task_name = task_id.rsplit(':', 1)
    with Lock(plan_uid, str(get_current_ident()), retries=20, wait=1):
        dg = graph.get_graph(plan_uid)
        dg.node[task_name]['status'] = status
        dg.node[task_name]['errmsg'] = errmsg
        dg.node[task_name]['end_time'] = time.time()

        schedule(plan_uid, dg)
