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

import random
import string

import pytest


@pytest.fixture
def address():
    return 'ipc:///tmp/solar_test_' + ''.join(
        (random.choice(string.ascii_lowercase) for x in xrange(4)))


@pytest.fixture
def tasks_address(address):
    return address + 'tasks'


@pytest.fixture
def system_log_address(address):
    return address + 'system_log'


@pytest.fixture
def scheduler_address(address):
    return address + 'scheduler'


@pytest.fixture
def timewatcher_address(address):
    return address + 'timewatcher'
