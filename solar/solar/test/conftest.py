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

import pytest
import time

from solar.core.resource import Resource
# from solar.interfaces import db

from solar.dblayer.model import get_bucket, ModelMeta, Model

@pytest.fixture
def resources():
    base_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'resource_fixtures')

    node_path = os.path.join(base_path, 'node')
    node1 = Resource('node1', node_path, args={'ip':'10.0.0.1'})
    node2 = Resource('node2', node_path, args={'ip':'10.0.0.2'})

    base_service_path = os.path.join(base_path, 'base_service')
    service1 = Resource('service1', base_service_path)
    return {'node1' : node1,
            'node2' : node2,
            'service1': service1
           }


@pytest.fixture(autouse=True)
def setup(request):

    for model in ModelMeta._defined_models:
        model.bucket = get_bucket(None, model, ModelMeta)


def pytest_runtest_teardown(item, nextitem):
    ModelMeta.session_end(result=True)
    return nextitem

def pytest_runtest_call(item):
    ModelMeta.session_start()

def patched_get_bucket_name(cls):
    return cls.__name__ + str(time.time())


Model.get_bucket_name = classmethod(patched_get_bucket_name)

from solar.dblayer.sql_client import SqlClient
client = SqlClient(':memory:', threadlocals=True, autocommit=False)

ModelMeta.setup(client)
