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

import gevent
import pytest

from solar.config import C
from solar.core.log import log
from solar.dblayer.model import ModelMeta
from solar.orchestration import executors
from solar.orchestration import extensions as loader
from solar.orchestration import workers


@pytest.fixture
def address(tmpdir):
    return 'ipc:///%s/' % tmpdir + ''.join(
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
def scheduler(request, scheduler_address):
    tasks_client = None

    if 'tasks' in request.node.fixturenames:
        tasks_client = executors.Client(
            request.getfuncargvalue('tasks_address'))

    worker = workers.scheduler.Scheduler(tasks_client)

    def session_end(ctxt):
        log.debug('Session end ID %s', id(gevent.getcurrent()))
        ModelMeta.session_end()

    def session_start(ctxt):
        log.debug('Session start ID %s', id(gevent.getcurrent()))
        ModelMeta.session_start()

    worker.for_all.before(session_start)
    worker.for_all.after(session_end)

    executor = executors.Executor(worker, scheduler_address)
    gevent.spawn(executor.run)
    return worker, executors.Client(scheduler_address)


@pytest.fixture
def tasks(request, tasks_address):
    worker = workers.tasks.Tasks()
    executor = executors.Executor(worker, tasks_address)
    worker.for_all.before(executor.register_task)
    if 'scheduler' in request.node.fixturenames:
        scheduler_client = workers.scheduler.SchedulerCallbackClient(
            executors.Client(request.getfuncargvalue(
                'scheduler_address')))
        worker.for_all.on_success(scheduler_client.update)
        worker.for_all.on_error(scheduler_client.error)

    gevent.spawn(executor.run)
    return worker, executors.Client(tasks_address)


@pytest.fixture
def clients(request):
    rst = {}
    rst['tasks'] = executors.Client(request.getfuncargvalue(
        'tasks_address'))
    rst['scheduler'] = executors.Client(request.getfuncargvalue(
        'scheduler_address'))
    rst['system_log'] = executors.Client(request.getfuncargvalue(
        'system_log_address'))
    return rst


@pytest.fixture
def extensions(clients):
    return loader.get_extensions(clients)


@pytest.fixture
def runner():
    return loader.get_runner(C.runner)


@pytest.fixture
def constructors():
    return loader.get_constructors()
