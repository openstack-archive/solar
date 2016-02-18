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

from solar.config import C  # NOQA
from solar.core.resource import composer
from solar.dblayer.model import clear_cache
from solar.errors import ExecutionTimeout
from solar import orchestration
from solar.orchestration.graph import wait_finish
from solar.orchestration.traversal import states
from solar.system_log import change
from solar.system_log import data


@pytest.fixture
def scheduler_client(scheduler_address):
    return orchestration.Client(scheduler_address)


@pytest.fixture(autouse=True)
def prepare_all(constructors, extensions, clients):
    for cons in constructors:
        gevent.spawn(cons.plugin, extensions, clients)


@pytest.fixture(autouse=True)
def resources(request, sequence_vr):
    scale = request.getfuncargvalue('scale')
    for idx in range(scale):
        composer.create(
            'sequence_%s' % idx, sequence_vr, inputs={'idx': idx})


@pytest.mark.skipif('"postgres" in C.solar_db')
@pytest.mark.parametrize('scale', [3])
def test_concurrent_sequences_with_no_handler(scale, clients):
    total_resources = scale * 3
    timeout = scale * 2
    scheduler_client = clients['scheduler']

    assert len(change.stage_changes()) == total_resources
    plan = change.send_to_orchestration()
    scheduler_client.next({}, plan.graph['uid'])

    def wait_function(timeout):
        try:
            for summary in wait_finish(plan.graph['uid'], timeout):
                assert summary[states.ERROR.name] == 0
                time.sleep(0.5)
        except ExecutionTimeout:
            pass
        return summary
    waiter = gevent.spawn(wait_function, timeout)
    waiter.join(timeout=timeout)
    res = waiter.get(block=True)
    assert res[states.SUCCESS.name] == total_resources
    assert len(data.CL()) == total_resources
    clear_cache()
    assert len(change.stage_changes()) == 0
