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

from mock import Mock
import networkx as nx
from pytest import fixture

from solar.orchestration import graph
from solar.orchestration import limits


@fixture
def t1():
    return Mock(name='t1',
                status='PENDING',
                target='1',
                resource_type='node',
                type_limit=2)


@fixture
def t2():
    return Mock(name='t2',
                status='PENDING',
                target='1',
                resource_type='node',
                type_limit=2)


@fixture
def t3():
    return Mock(name='t3',
                status='PENDING',
                target='1',
                resource_type='node',
                type_limit=2)


@fixture
def dg(t1, t2, t3):
    example = nx.DiGraph()
    example.add_nodes_from((t1, t2, t3))
    return example


def test_target_rule(dg, t1, t2):
    assert limits.target_based_rule(dg, [], t1)
    assert limits.target_based_rule(dg, [t1], t2) is False


def test_type_limit_rule(dg, t1, t2, t3):
    assert limits.type_based_rule(dg, [t1], t2)
    assert limits.type_based_rule(dg, [t1, t2], t3) is False


def test_items_rule(dg):
    assert limits.items_rule(dg, [t1] * 99, t2)
    assert limits.items_rule(dg, [t1] * 99, t2, limit=10) is False


def test_filtering_chain(dg, t1, t2):

    chain = limits.get_default_chain(dg, [], [t1, t2])
    assert list(chain) == [t1]


@fixture
def seq_plan():
    seq_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'orch_fixtures',
        'sequential.yaml')
    return graph.create_plan(seq_path)


def test_limits_sequential(seq_plan):
    stack_to_execute = seq_plan.nodes()
    while stack_to_execute:
        left = stack_to_execute[0]
        assert list(limits.get_default_chain(seq_plan, [],
                                             stack_to_execute)) == [left]
        stack_to_execute.pop(0)
