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

from functools import partial
import time

from solar.core.log import log
from solar.dblayer.locking import Lock
from solar.dblayer.locking import Waiter
from solar.orchestration import graph
from solar.orchestration import limits
from solar.orchestration.traversal import states
from solar.orchestration.traversal import find_visitable_tasks
from solar.orchestration.traversal import VISITED
from solar.orchestration.workers import base
from solar.utils import get_current_ident


class Scheduler(base.Worker):

    def __init__(self, tasks_client):
        self._tasks = tasks_client
        super(Scheduler, self).__init__()

    def _next(self, plan):
        return list(limits.get_default_chain(
            plan,
            [t for t in plan if t.status == states.INPROGRESS.name],
            find_visitable_tasks(plan)))

    def next(self, ctxt, plan_uid):
        with Lock(
                plan_uid,
                str(get_current_ident()),
                retries=20,
                waiter=Waiter(1)
        ):
            log.debug('Received *next* event for %s', plan_uid)
            plan = graph.get_graph(plan_uid)
            if len(plan) == 0:
                raise ValueError('Plan {} is empty'.format(plan_uid))
            rst = self._next(plan)
            for task in rst:
                self._do_scheduling(plan, task)
            log.debug('Scheduled tasks %r', rst)
            return rst

    def soft_stop(self, ctxt, plan_uid):
        with Lock(
                plan_uid,
                str(get_current_ident()),
                retries=20,
                waiter=Waiter(1)
        ):
            plan = graph.get_graph(plan_uid)
            for task in plan:
                if task.status in (
                        states.PENDING.name, states.ERROR_RETRY.name):
                    task.status = states.SKIPPED.name
                    task.save_lazy()

    def _do_update(self, task, status, errmsg=''):
        """For single update correct state and other relevant data."""
        if task.status in VISITED:
            log.debug(
                'Task %s already in visited status %s'
                ', skipping update to %s',
                task.name, task.status, status)
            return

        if status == states.ERROR.name and task.retry > 0:
            task.retry -= 1
            status = states.ERROR_RETRY.name
            log.debug('Retry task %s in plan %s, retries left %s',
                      task.name, task.execution, task.retry)
        else:
            task.end_time = time.time()
        task.status = status
        task.errmsg = errmsg
        task.save_lazy()

    def _do_scheduling(self, task):
        task.status = states.INPROGRESS.name
        task.start_time = time.time()
        ctxt = {
            'task_id': task.key,
            'task_name': task.name,
            'plan_uid': task.execution,
            'timelimit': task.timelimit,
            'timeout': task.timeout}
        log.debug(
            'Timelimit for task %s - %s, timeout - %s',
            task, task.timelimit, task.timeout)
        task.save_lazy()
        self._tasks(
            task.type, ctxt,
            *task.args)
        if timeout:
            self._configure_timeout(ctxt, task.timeout)

    def update_next(self, ctxt, status, errmsg):
        log.debug(
            'Received update for TASK %s - %s %s',
            ctxt['task_id'], status, errmsg)
        plan_uid, task_name = ctxt['task_id'].rsplit('~', 1)
        with Lock(
                plan_uid,
                str(get_current_ident()),
                retries=20,
                waiter=Waiter(1)
        ):
            plan = graph.get_subgraph_based_on_task(plan_uid, task_name)
            task = plan.node[ctxt['task_id']]
            self._do_update(plan, task, status, errmsg=errmsg)
            rst = self._next(plan)
            for task_name in rst:
                self._do_scheduling(plan, task)
            log.debug('Scheduled tasks %r', rst)
            return rst

    def _configure_timeout(self, ctxt, timeout):
        if not hasattr(self._executor, 'register_timeout'):
            raise NotImplemented('Timeout is not supported')
        self._executor.register_timeout(
            timeout,
            partial(self.update_next, ctxt,
                    states.ERROR.name, 'Timeout Error'))


class SchedulerCallbackClient(object):

    def __init__(self, client):
        self.client = client

    def update(self, ctxt, result, *args, **kwargs):
        self.client.update_next(ctxt, states.SUCCESS.name, '')

    def error(self, ctxt, result, *args, **kwargs):
        self.client.update_next(ctxt, states.ERROR.name, repr(result))


def tasks_subscribe(tasks, clients):
    log.debug('Scheduler subscribes to tasks hooks')
    scheduler = SchedulerCallbackClient(clients['scheduler'])
    tasks.for_all.on_success(scheduler.update)
    tasks.for_all.on_error(scheduler.error)
