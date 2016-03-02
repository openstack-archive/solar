#    Copyright 2016 Mirantis, Inc.
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

import pytest

from solar.orchestration import graph
from solar.orchestration.traversal import states
from solar.orchestration.workers.scheduler import Scheduler


def test_scheduler_next_fails_with_empty_plan():
    scheduler = Scheduler(None)
    with pytest.raises(ValueError):
        scheduler.next({}, 'nonexistent_uid')


def test_soft_stop(simple_plan):
    # graph.save_graph(simple_plan)
    uid = simple_plan.graph['uid']

    scheduler = Scheduler(None)
    scheduler.soft_stop({}, uid)

    plan = graph.get_graph(uid)
    for n in plan:
        assert plan.node[n]['status'] == states.SKIPPED.name
