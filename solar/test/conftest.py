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
import os
import time

import pytest

from solar.core.resource.repository import Repository
from solar.core.resource import Resource
from solar.dblayer.model import get_bucket
from solar.dblayer.model import Model
from solar.dblayer.model import ModelMeta
from solar.orchestration import graph


def patched_get_bucket_name(cls):
    return cls.__name__ + str(os.getpid()) + str(time.time())


@pytest.fixture
def resources():
    base_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'resource_fixtures')

    node_path = os.path.join(base_path, 'node')
    node1 = Resource('node1', node_path, args={'ip': '10.0.0.1'})
    node2 = Resource('node2', node_path, args={'ip': '10.0.0.2'})

    base_service_path = os.path.join(base_path, 'base_service')
    service1 = Resource('service1', base_service_path)
    return {'node1': node1,
            'node2': node2,
            'service1': service1
            }


@pytest.fixture(autouse=True)
def setup(request):

    for model in ModelMeta._defined_models:
        model.bucket = get_bucket(None, model, ModelMeta)


@pytest.fixture(scope='session', autouse=True)
def repos_path(tmpdir_factory):
    Repository._REPOS_LOCATION = str(tmpdir_factory.mktemp('repositories'))
    path = Repository._REPOS_LOCATION
    repo = Repository('resources')
    repo.create(path)


def pytest_runtest_teardown(item, nextitem):
    ModelMeta.session_end(result=True)
    return nextitem

# It will run before all fixtures


def pytest_runtest_setup(item):
    ModelMeta.session_start()

# it will run after fixtures but before test


def pytest_runtest_call(item):
    ModelMeta.session_end()
    ModelMeta.session_start()


Model.get_bucket_name = classmethod(patched_get_bucket_name)


def plan_from_fixture(name):
    riak_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'orch_fixtures',
        '%s.yaml' % name)
    return graph.create_plan(riak_path)


@pytest.fixture
def riak_plan():
    return plan_from_fixture('riak')


@pytest.fixture
def simple_plan():
    return plan_from_fixture('simple')


@pytest.fixture
def sequential_plan():
    return plan_from_fixture('sequential')


@pytest.fixture
def two_path_plan():
    return plan_from_fixture('two_path')


@pytest.fixture
def timelimit_plan():
    return plan_from_fixture('timelimit')


@pytest.fixture
def sequence_vr(tmpdir):
    base_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'resource_fixtures')
    vr_tmpl_path = os.path.join(base_path, 'sequence.yaml.tmpl')
    base_resource_path = os.path.join(base_path, 'data_resource')
    with open(vr_tmpl_path) as f:
        vr_data = f.read().format(
            resource_path=base_resource_path,
            idx='#{ idx }#')
    vr_file = tmpdir.join('sequence.yaml')
    vr_file.write(vr_data)
    return str(vr_file)
