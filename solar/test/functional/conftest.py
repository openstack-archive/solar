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


from solar.core.log import log
from solar.dblayer.model import ModelMeta
from solar.orchestration.executors import zerorpc_executor
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
        tasks_client = zerorpc_executor.Client(
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

    executor = zerorpc_executor.Executor(worker, scheduler_address)
    gevent.spawn(executor.run)
    return worker, zerorpc_executor.Client(scheduler_address)


@pytest.fixture
def tasks(request, tasks_address):
    worker = workers.tasks.Tasks()
    executor = zerorpc_executor.Executor(worker, tasks_address)
    worker.for_all.before(executor.register)
    if 'scheduler' in request.node.fixturenames:
        scheduler_client = workers.scheduler.SchedulerCallbackClient(
            zerorpc_executor.Client(request.getfuncargvalue(
                'scheduler_address')))
        worker.for_all.on_success(scheduler_client.update)
        worker.for_all.on_error(scheduler_client.error)

    gevent.spawn(executor.run)
    return worker, zerorpc_executor.Client(tasks_address)
