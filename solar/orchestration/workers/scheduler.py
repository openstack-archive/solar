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

import time

from solar.core.log import log
from solar.dblayer.locking import Lock
from solar.orchestration import graph
from solar.orchestration import limits
from solar.orchestration.traversal import states
from solar.orchestration.traversal import traverse
from solar.orchestration.traversal import VISITED
from solar.orchestration.workers import base
from solar.utils import get_current_ident


class Scheduler(base.Worker):

    def __init__(self, tasks_client, timewatcher):
        self._tasks = tasks_client
        self._timewatcher = timewatcher
        super(Scheduler, self).__init__()

    def _next(self, plan):
        tasks = traverse(plan)
        filtered_tasks = list(limits.get_default_chain(
            plan,
            [t for t in plan
             if plan.node[t]['status'] == states.INPROGRESS.name],
            tasks))
        return filtered_tasks

    def next(self, ctxt, plan_uid):
        with Lock(plan_uid, str(get_current_ident()), retries=20, wait=1):
            log.debug('Received *next* event for %s', plan_uid)
            plan = graph.get_graph(plan_uid)
            rst = self._next(plan)
            for task_name in rst:
                self._do_scheduling(plan, task_name)
            graph.update_graph(plan)
            log.debug('Scheduled tasks %r', rst)
            # process tasks with tasks client
            return rst

    def soft_stop(self, ctxt, plan_uid):
        with Lock(plan_uid, str(get_current_ident()), retries=20, wait=1):
            plan = graph.get_graph(plan_uid)
            for n in plan:
                if plan.node[n]['status'] in (
                        states.PENDING.name, states.PENDING_RETRY.name):
                    plan.node[n]['status'] = states.SKIPPED.name
            graph.update_graph(plan)

    def _do_update(self, plan, task_name, status, errmsg=''):
        """For single update correct state and other relevant data."""
        old_status = plan.node[task_name]['status']
        if old_status in VISITED:
            return
        retries_count = plan.node[task_name]['retry']

        if status == states.ERROR.name and retries_count > 0:
            retries_count -= 1
            status = states.ERROR_RETRY.name
            log.debug('Retry task %s in plan, retries left %s',
                      task_name, plan.graph['uid'], retries_count)
        else:
            plan.node[task_name]['end_time'] = time.time()
        plan.node[task_name]['status'] = status
        plan.node[task_name]['errmsg'] = errmsg
        plan.node[task_name]['retry'] = retries_count

    def _do_scheduling(self, plan, task_name):
        task_id = '{}:{}'.format(plan.graph['uid'], task_name)
        task_type = plan.node[task_name]['type']
        plan.node[task_name]['status'] = states.INPROGRESS.name
        ctxt = {
            'task_id': task_id,
            'task_name': task_name,
            'plan_uid': plan.graph['uid']}
        self._tasks(
            task_type, ctxt,
            *plan.node[task_name]['args'])
        timelimit = plan.node[task_name].get('timelimit', 0)
        if timelimit:
            log.debug(
                'Timelimit for task %s will be %s',
                task_id, timelimit)
            self._timewatcher.timelimit(ctxt, task_id, timelimit)

    def update_next(self, ctxt, status, errmsg):
        log.debug(
            'Received update for TASK %s - %s %s',
            ctxt['task_id'], status, errmsg)
        plan_uid, task_name = ctxt['task_id'].rsplit(':', 1)
        with Lock(plan_uid, str(get_current_ident()), retries=20, wait=1):
            plan = graph.get_graph(plan_uid)
            self._do_update(plan, task_name, status, errmsg=errmsg)
            rst = self._next(plan)
            for task_name in rst:
                self._do_scheduling(plan, task_name)
            graph.update_graph(plan)
            log.debug('Scheduled tasks %r', rst)
            return rst


class SchedulerCallbackClient(object):

    def __init__(self, client):
        self.client = client

    def update(self, ctxt, result, *args, **kwargs):
        self.client.update_next(ctxt, states.SUCCESS.name, '')

    def error(self, ctxt, result, *args, **kwargs):
        self.client.update_next(ctxt, states.ERROR.name, repr(result))
