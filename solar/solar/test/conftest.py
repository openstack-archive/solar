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

from solar.core.resource import Resource
from solar.interfaces import db

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


def pytest_configure():
    if db.CURRENT_DB == 'redis_graph_db':
        db.DB = db.get_db(backend='fakeredis_graph_db')
    elif db.CURRENT_DB == 'redis_db':
        db.DB = db.get_db(backend='fakeredis_db')
    else:
        db.DB = db.get_db(backend=db.CURRENT_DB)


@pytest.fixture(autouse=True)
def cleanup(request):

    def fin():
        db.get_db().clear()

    request.addfinalizer(fin)
