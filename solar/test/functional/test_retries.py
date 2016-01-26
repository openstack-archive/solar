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

import gevent
import mock
import pytest

from solar.core.log import log
from solar.dblayer.model import ModelMeta
from solar.orchestration.executors import zerorpc_executor
from solar.orchestration import graph
from solar.orchestration.traversal import states
from solar.orchestration.workers import scheduler as wscheduler
from solar.orchestration.workers import tasks as wtasks


@pytest.fixture
def simple_plan_retries(simple_plan):
    simple_plan.node['just_fail']['retry'] = 1
    graph.update_graph(simple_plan, force=True)
    return simple_plan


@pytest.fixture
def scheduler(request, scheduler_address):
    tasks_client = None
    if 'tasks' in request.node.fixturenames:
        tasks_client = zerorpc_executor.Client(
            request.getfuncargvalue('tasks_address'))
    worker = wscheduler.Scheduler(tasks_client)

    def session_end(ctxt):
        log.debug('Session end ID %s', id(gevent.getcurrent()))
        ModelMeta.session_end()

    def session_start(ctxt):
        log.debug('Session start ID %s', id(gevent.getcurrent()))
        ModelMeta.session_start()

    worker.for_all.before(session_start)
    worker.for_all.after(session_end)

    executor = zerorpc_executor.Executor(worker, scheduler_address)
    gevent.spawn(executor.run)
    return worker, zerorpc_executor.Client(scheduler_address)


@pytest.fixture
def tasks(request, tasks_address):
    worker = wtasks.Tasks()
    executor = zerorpc_executor.Executor(worker, tasks_address)

    if 'scheduler' in request.node.fixturenames:
        scheduler_client = wscheduler.SchedulerCallbackClient(
            zerorpc_executor.Client(request.getfuncargvalue(
                'scheduler_address')))
        worker.for_all.on_success(scheduler_client.update)
        worker.for_all.on_error(scheduler_client.error)

    gevent.spawn(executor.run)
    return worker, zerorpc_executor.Client(tasks_address)


def test_retry_just_fail(scheduler, tasks, simple_plan_retries):
    timeout = 3
    plan = simple_plan_retries
    worker, client = scheduler
    tracer = mock.Mock()
    worker.for_all.on_success(tracer.update)

    def wait_function(timeout):
        for summary in graph.wait_finish(plan.graph['uid'], timeout):
            assert summary[states.ERROR.name] <= 1
            time.sleep(0.5)
        return summary
    client.next({}, plan.graph['uid'])
    waiter = gevent.spawn(wait_function, timeout)
    waiter.join(timeout=timeout)
    assert len(tracer.update.call_args_list) == 4
    for call in tracer.update.call_args_list[2:]:
        args, _ = call
        ctxt, rst, status, msg = args
        assert ctxt['task_name'] == 'just_fail'
        assert status == states.ERROR.name
