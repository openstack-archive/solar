
import random
import string
import gevent

import pytest
import zerorpc
import mock

from solar.dblayer.model import ModelMeta
from solar.dblayer.model import Model
from solar.dblayer.model import get_bucket

from solar.orchestration.workers import scheduler as wscheduler
from solar.orchestration.workers import tasks as wtasks
from solar.orchestration.executors import zerorpc_executor
from solar.orchestration.workers import base


@pytest.fixture
def address():
    return 'ipc:///tmp/solar_test_' + ''.join(
        (random.choice(string.ascii_lowercase) for x in xrange(4)))


@pytest.fixture
def tracer(request):
    return mock.Mock()


@pytest.fixture
def tasks(address):
    server = gevent.spawn(wtasks.run, address)
    client = wtasks.client(address)
    assert client('ping', {}) == 'pong'
    return client


@pytest.fixture
def scheduler(request, tracer, address):
    server = gevent.spawn(wscheduler.run, address, tracer)
    client = wscheduler.client(address)
    assert client('ping', {}) == 'pong'
    return client
