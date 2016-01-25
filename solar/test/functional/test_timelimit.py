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

from solar.errors import ExecutionTimeout
from solar.orchestration import graph
from solar.orchestration.traversal import states


def test_timelimit_plan(timelimit_plan, scheduler, tasks, timewatcher):
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
