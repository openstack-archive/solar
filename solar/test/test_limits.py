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

from pytest import fixture
import networkx as nx

from solar.orchestration import limits
from solar.orchestration import graph


@fixture
def dg():
    ex = nx.DiGraph()
    ex.add_node('t1', status='PENDING', target='1',
                resource_type='node', type_limit=2)
    ex.add_node('t2', status='PENDING', target='1',
                resource_type='node', type_limit=2)
    ex.add_node('t3', status='PENDING', target='1',
                resource_type='node', type_limit=2)
    return ex


def test_target_rule(dg):

    assert limits.target_based_rule(dg, [], 't1') == True
    assert limits.target_based_rule(dg, ['t1'], 't2') == False


def test_type_limit_rule(dg):
    assert limits.type_based_rule(dg, ['t1'], 't2') == True
    assert limits.type_based_rule(dg, ['t1', 't2'], 't3') == False


def test_items_rule(dg):

    assert limits.items_rule(dg, ['1'] * 99, '2')
    assert limits.items_rule(dg, ['1'] * 99, '2', limit=10) == False


@fixture
def target_dg():
    ex = nx.DiGraph()
    ex.add_node('t1', status='PENDING', target='1')
    ex.add_node('t2', status='PENDING', target='1')

    return ex


def test_filtering_chain(target_dg):

    chain = limits.get_default_chain(target_dg, [], ['t1', 't2'])
    assert list(chain) == ['t1']


@fixture
def seq_plan():
    seq_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'orch_fixtures',
        'sequential.yaml')
    return graph.create_plan(seq_path, save=False)


def test_limits_sequential(seq_plan):
    stack_to_execute = seq_plan.nodes()
    while stack_to_execute:
        left = stack_to_execute[0]
        assert list(limits.get_default_chain(
            seq_plan, [], stack_to_execute)) == [left]
        stack_to_execute.pop(0)
