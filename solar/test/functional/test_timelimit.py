#
# Copyright 2015 Mirantis, Inc.
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
#

import time

import gevent
import pytest

from solar.dblayer import ModelMeta
from solar.errors import ExecutionTimeout
from solar.orchestration import Client
from solar.orchestration import Executor
from solar.orchestration import graph
from solar.orchestration.traversal import states
from solar.orchestration import workers


@pytest.fixture(autouse=True)
def scheduler(scheduler_address, tasks_address, timewatcher_address):
    timewatcher = Client(timewatcher_address)
    scheduler = workers.Scheduler(Client(tasks_address), timewatcher)
    scheduler_executor = Executor(scheduler, scheduler_address)
    scheduler.for_all.before(lambda ctxt: ModelMeta.session_start())
    scheduler.for_all.after(lambda ctxt: ModelMeta.session_end())
    gevent.spawn(scheduler_executor.run)


@pytest.fixture(autouse=True)
def tasks(tasks_address, scheduler_address):
    scheduler = workers.SchedulerCallbackClient(
        Client(scheduler_address))
    tasks = workers.Tasks()
    tasks_executor = Executor(tasks, tasks_address)
    tasks.for_all.before(tasks_executor.register)
    tasks.for_all.on_success(scheduler.update)
    tasks.for_all.on_error(scheduler.error)
    gevent.spawn(tasks_executor.run)


@pytest.fixture(autouse=True)
def timewatcher(tasks_address, scheduler_address, timewatcher_address):
    tasks = Client(tasks_address)
    scheduler = Client(scheduler_address)
    time_worker = workers.TimeWatcher(tasks, scheduler)
    gevent.spawn(Executor(time_worker, timewatcher_address).run)


@pytest.fixture
def scheduler_client(scheduler_address):
    return Client(scheduler_address)


def test_timelimit_plan(timelimit_plan, scheduler_client):
    scheduler_client.next({}, timelimit_plan.graph['uid'])

    def wait_function(timeout):
        try:
            for summary in graph.wait_finish(
                    timelimit_plan.graph['uid'], timeout):
                time.sleep(0.5)
        except ExecutionTimeout:
            return summary
    waiter = gevent.spawn(wait_function, 3)
    waiter.join(timeout=3)
    finished_plan = graph.get_graph(timelimit_plan.graph['uid'])
    assert 'ExecutionTimeout' in finished_plan.node['t1']['errmsg']
    assert finished_plan.node['t2']['status'] == states.PENDING.name
