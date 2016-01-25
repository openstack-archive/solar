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
import pytest

from solar.core.log import log
from solar.dblayer.model import ModelMeta
from solar.orchestration.executors import zerorpc_executor
from solar.orchestration.workers import scheduler as wscheduler
from solar.orchestration.workers import tasks as wtasks


@pytest.fixture
def tasks_worker():
    return wtasks.Tasks()


@pytest.fixture
def tasks_for_scheduler(request, tasks_worker, address):
    address = address + 'tasks'
    executor = zerorpc_executor.Executor(tasks_worker, address)
    gevent.spawn(executor.run)
    return zerorpc_executor.Client(address)


@pytest.fixture
def scheduler(tasks_for_scheduler, scheduler_address):
    address = scheduler_address
    worker = wscheduler.Scheduler(tasks_for_scheduler, None)

    def session_end(ctxt):
        log.debug('Session end ID %s', id(gevent.getcurrent()))
        ModelMeta.session_end()

    def session_start(ctxt):
        log.debug('Session start ID %s', id(gevent.getcurrent()))
        ModelMeta.session_start()

    worker.for_all.before(session_start)
    worker.for_all.after(session_end)

    executor = zerorpc_executor.Executor(worker, address)
    gevent.spawn(executor.run)
    return worker, zerorpc_executor.Client(address)


@pytest.fixture(autouse=True)
def setup_scheduler_callback(scheduler, tasks_worker):
    worker, client = scheduler
    scheduler_client = wscheduler.SchedulerCallbackClient(
        zerorpc_executor.Client(client.connect_to))
    tasks_worker.for_all.on_success(scheduler_client.update)
    tasks_worker.for_all.on_error(scheduler_client.update)


def _wait_scheduling(plan, wait_time, waiter, client):
    client.next({}, plan.graph['uid'])
    waiter = gevent.spawn(waiter)
    waiter.join(timeout=wait_time)


def test_simple_fixture(simple_plan, scheduler):
    worker, client = scheduler
    scheduling_results = []
    expected = [['echo_stuff'], ['just_fail'], []]

    def register(ctxt, rst, *args, **kwargs):
        scheduling_results.append(rst)
    worker.for_all.on_success(register)

    def _result_waiter():
        while scheduling_results != expected:
            time.sleep(0.1)
    _wait_scheduling(simple_plan, 3, _result_waiter, client)
    assert scheduling_results == expected


def test_sequential_fixture(sequential_plan, scheduler):
    worker, client = scheduler
    scheduling_results = set()
    expected = {('s1',), ('s2',), ('s3',), ()}

    def register(ctxt, rst, *args, **kwargs):
        scheduling_results.add(tuple(rst))
    worker.for_all.on_success(register)

    def _result_waiter():
        while scheduling_results != expected:
            time.sleep(0.1)
    _wait_scheduling(sequential_plan, 2, _result_waiter, client)
    assert scheduling_results == expected


def test_two_path_fixture(two_path_plan, scheduler):
    worker, client = scheduler
    scheduling_results = set()
    expected = {'a', 'b', 'c', 'd', 'e'}

    def register(ctxt, rst, *args, **kwargs):
        if 'task_name' in ctxt:
            scheduling_results.add(ctxt['task_name'])
    worker.for_all.on_success(register)

    def _result_waiter():
        while len(scheduling_results) != len(expected):
            time.sleep(0.1)
    _wait_scheduling(two_path_plan, 3, _result_waiter, client)
    assert scheduling_results == expected
