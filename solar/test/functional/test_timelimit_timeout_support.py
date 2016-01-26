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
    assert 'ExecutionTimeout' in finished_plan.node['t1']['errmsg']
    assert finished_plan.node['t2']['status'] == states.PENDING.name


@pytest.fixture
def timeout_plan(simple_plan):
    simple_plan.node['echo_stuff']['timeout'] = 1
    graph.update_graph(simple_plan, force=True)
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
    assert (timeout_plan.node['echo_stuff']['status']
            == states.ERROR.name)
