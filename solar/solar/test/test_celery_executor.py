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

import networkx as nx
from pytest import fixture
from mock import patch

from solar.orchestration import executor


@fixture
def dg():
    ex = nx.DiGraph()
    ex.add_node('t1', args=['t'], status='PENDING', type='echo')
    ex.graph['uid'] = 'some_string'
    return ex


@patch.object(executor, 'app')
def test_celery_executor(mapp, dg):
    """Just check that it doesnt fail for now.
    """
    assert executor.celery_executor(dg, ['t1'])
    assert dg.node['t1']['status'] == 'INPROGRESS'
