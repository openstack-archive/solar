

import time
import gevent
import pytest
from mock import call

from solar.orchestration.executors import zerorpc_executor
from solar.orchestration.workers import tasks as wtasks
from solar.orchestration.workers import scheduler as wscheduler
from solar.dblayer.model import ModelMeta


@pytest.fixture
def tasks_worker():
    return wtasks.Tasks()


@pytest.fixture
def tasks_for_scheduler(tasks_worker, address):
    address = address + 'tasks'
    executor = zerorpc_executor.Executor(tasks_worker, address)
    gevent.spawn(executor.run)
    return zerorpc_executor.Client(address)


@pytest.fixture
def scheduler(tasks_for_scheduler, address):
    address = address + 'scheduler'
    worker = wscheduler.Scheduler(tasks_for_scheduler)
    worker.for_all.before(ModelMeta.session_start)
    worker.for_all.after(ModelMeta.session_end)
    executor = zerorpc_executor.Executor(worker, address)
    gevent.spawn(executor.run)
    return worker, zerorpc_executor.Client(address)


@pytest.fixture(autouse=True)
def setup_scheduler_callback(scheduler, tasks_worker):
    worker, client = scheduler
    scheduler_client = wscheduler.SchedulerCallbackClient(
        zerorpc_executor.Client(client.connect_to))
    tasks_worker.for_all.on_success(scheduler_client.update)
    tasks_worker.for_all.on_error(scheduler_client.update)


def test_scheduling_simple_plan(scheduler, simple_plan):
    worker, client = scheduler
    scheduling_results = []
    def register(ctxt, rst, *args, **kwargs):
        scheduling_results.append(rst)
    worker.for_all.on_success(register)
    client.next({}, simple_plan.graph['uid'])
    expected = [['echo_stuff'], ['just_fail'], []]
    def _result_waiter():
        while scheduling_results != expected:
            time.sleep(0.1)
    waiter = gevent.spawn(_result_waiter)
    waiter.join(timeout=3)
    assert scheduling_results == expected
