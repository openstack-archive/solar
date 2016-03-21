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
from mock import Mock

from solar.orchestration import graph


def test_concurrent_tasks_choice_based_on_weights(
        scheduler, tasks, concurrent_choice_plan):
    worker, client = scheduler
    tracer = Mock()
    plan = concurrent_choice_plan
    worker.next.on_success(tracer.update)
    worker.update_next.on_success(tracer.update)

    def wait_function(timeout):
        for summary in graph.wait_finish(plan.graph['uid'], timeout):
            time.sleep(0.5)
        return summary
    client.next({}, concurrent_choice_plan.graph['uid'])
    waiter = gevent.spawn(wait_function, 2)
    waiter.join(timeout=3)
    first_call = tracer.update.call_args_list[0]
    args, _ = first_call
    ctxt, rst, _ = args
    assert len(rst) == 1
    assert rst[0].name == 's2'
    second_call = tracer.update.call_args_list[1]
    args, _ = second_call
    ctxt, rst, status, msg = args
    assert len(rst) == 2
    assert {t.name for t in rst} == {'s1', 's3'}
