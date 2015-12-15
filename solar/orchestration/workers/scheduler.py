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

from solar.orchestration import graph
from solar.orchestration.workers import base
from solar.dblayer.locking import Lock
from solar.utils import get_current_ident
from solar.orchestration.traversal import traverse
from solar.orchestration import limits
from solar.core.log import log


class Scheduler(base.Worker):

    def __init__(self, tasks_client):
        self._tasks = tasks_client
        super(Scheduler, self).__init__()

    def _next(self, dg):
        tasks = traverse(dg)
        filtered_tasks = list(limits.get_default_chain(
            dg,
            [t for t in dg if dg.node[t]['status'] == 'INPROGRESS'],
            tasks))
        return filtered_tasks

    def next(self, ctxt, plan_uid):
        with Lock(plan_uid, str(get_current_ident()), retries=20, wait=1):
            log.debug('Received *next* event for %s', plan_uid)
            dg = graph.get_graph(plan_uid)
            rst = self._next(dg)
            for task_name in rst:
                task_id = '{}:{}'.format(dg.graph['uid'], task_name)
                task_type = dg.node[task_name]['type']
                dg.node[task_name]['status'] = 'INPROGRESS'
                ctxt = {'task_id': task_id}
                self._tasks(
                    task_type, ctxt,
                    dg.node[task_name]['args'])
            graph.update_graph(dg)
            log.debug('Scheduled tasks %r', rst)
            # process tasks with tasks client
            return rst

    def soft_stop(self, ctxt, plan_uid):
        with Lock(plan_uid, str(get_current_ident()), retries=20, wait=1):
            dg = graph.get_graph(plan_uid)
            for n in dg:
                if dg.node[n]['status'] == 'PENDING':
                    dg.node[n]['status'] = 'SKIPPED'
            graph.update_graph(dg)

    def update_next(self, ctxt, status, errmsg=''):
        plan_uid, task_name = ctxt['task_id'].rsplit(':', 1)
        with Lock(plan_uid, str(get_current_ident()), retries=20, wait=1):
            dg = graph.get_graph(plan_uid)
            dg.node[task_name]['status'] = status
            dg.node[task_name]['errmsg'] = errmsg
            dg.node[task_name]['end_time'] = time.time()
            rst = self._next(dg)
            for task_name in rst:
                task_id = '{}:{}'.format(dg.graph['uid'], task_name)
                task_type = dg.node[task_name]['type']
                dg.node[task_name]['status'] = 'INPROGRESS'
                ctxt = {'task_id': task_id}
                self._tasks(
                    task_type, ctxt,
                    dg.node[task_name]['args'])
            graph.update_graph(dg)
            log.debug('Scheduled tasks %r', rst)
            return rst


class SchedulerCallbackClient(object):

    def __init__(self, client):
        self.client = client

    def update(self, ctxt, result, *args, **kwargs):
        if isinstance(result, Exception):
            self.client.update_next(ctxt, 'ERROR', errmsg=str(result))
        else:
            self.client.update_next(ctxt, 'SUCCESS')


def client(connect_to):
    from solar.orchestration.executors import zerorpc_executor
    return zerorpc_executor.Client(connect_to)


def run(bind_to, tasks_client):
    from solar.orchestration.executors import zerorpc_executor
    zerorpc_executor.Executor(
        Scheduler(tasks_client), bind_to).run()
