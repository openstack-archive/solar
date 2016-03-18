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
import mock
import pytest

from solar.errors import ExecutionTimeout
from solar.orchestration import graph
from solar.orchestration.traversal import states


def test_timelimit_plan(timelimit_plan, scheduler, tasks):
    worker, client = scheduler
    client.next({}, timelimit_plan.graph['uid'])

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
    t1 = graph.get_task_by_name(finished_plan, 't1')
    t2 = graph.get_task_by_name(finished_plan, 't2')
    assert 'ExecutionTimeout' in t1.errmsg
    assert t2.status == states.PENDING.name


@pytest.fixture
def timeout_plan(simple_plan):
    echo_task = graph.get_task_by_name(simple_plan, 'echo_stuff')
    echo_task.timeout = 1
    echo_task.save()
    return simple_plan


def test_timeout_plan(timeout_plan, scheduler):
    worker, client = scheduler
    worker._tasks = mock.Mock()
    client.next({}, timeout_plan.graph['uid'])

    def wait_function(timeout):
        for summary in graph.wait_finish(
                timeout_plan.graph['uid'], timeout):
            if summary[states.ERROR.name] == 1:
                return summary
            time.sleep(0.3)
        return summary
    waiter = gevent.spawn(wait_function, 2)
    waiter.get(block=True, timeout=2)
    timeout_plan = graph.get_graph(timeout_plan.graph['uid'])
    echo_task = graph.get_task_by_name(timeout_plan, 'echo_stuff')
    assert echo_task.status == states.ERROR.name
