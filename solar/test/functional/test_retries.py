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

from solar.orchestration import graph
from solar.orchestration.traversal import states


@pytest.fixture
def simple_plan_retries(simple_plan):
    fail_task = next(t for t in simple_plan.nodes()
                     if t.name == 'just_fail')
    fail_task.retry = 1
    fail_task.save()
    return simple_plan


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
