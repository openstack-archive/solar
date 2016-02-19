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

import gevent
import pytest
import time

from solar.config import C  # NOQA


def _wait_scheduling(plan, wait_time, waiter, client):
    client.next({}, plan.graph['uid'])
    waiter = gevent.spawn(waiter)
    waiter.join(timeout=wait_time)


def test_simple_fixture(simple_plan, scheduler, tasks):
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


def test_sequential_fixture(sequential_plan, scheduler, tasks):
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


# TODO: see this bug https://bugs.launchpad.net/solar/+bug/1546992
# this test is skipped only with postgres backend
# this is temporary situation
@pytest.mark.skipif('"postgres" in C.solar_db')
def test_two_path_fixture(two_path_plan, scheduler, tasks):
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
