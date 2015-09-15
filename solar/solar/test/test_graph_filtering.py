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
from pytest import mark
import networkx as nx

from solar.orchestration import graph
from solar.orchestration import filters
from solar.orchestration.traversal import states
from solar.utils import yaml_load


@fixture
def dg_ex1():
    dg = nx.DiGraph()
    dg.add_nodes_from(['n1', 'n2', 'n3', 'n4', 'n5'])
    dg.add_path(['n1', 'n5'])
    dg.add_path(['n3', 'n5'])
    dg.add_path(['n1', 'n2', 'n4'])
    return dg


@mark.parametrize("end_nodes,visited", [
    (['n5'], {'n1', 'n3', 'n5'}),
    (['n4'], {'n1', 'n2', 'n4'}),
    (['n4', 'n5'], {'n1', 'n2', 'n3', 'n4', 'n5'}),
])
def test_end_at(dg_ex1, end_nodes, visited):
    assert set(filters.end_at(dg_ex1, end_nodes)) == visited

@mark.parametrize("start_nodes,visited", [
    (['n3'], {'n3'}),
    (['n1'], {'n1', 'n2', 'n4'}),
    (['n1', 'n3'], {'n1', 'n2', 'n3', 'n4', 'n5'})
])
def test_start_from(dg_ex1, start_nodes, visited):
    assert set(filters.start_from(dg_ex1, start_nodes)) == visited

@fixture
def dg_ex2():
    dg = nx.DiGraph()
    dg.add_nodes_from(['n1', 'n2', 'n3', 'n4', 'n5'])
    dg.add_edges_from([('n1', 'n3'), ('n2', 'n3'), ('n3', 'n4'), ('n3', 'n5')])
    return dg


@fixture
def riak_plan():
    riak_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'orch_fixtures',
        'riak.yaml')
    return graph.create_plan(riak_path, save=False)


def test_riak_start_node1(riak_plan):
    assert filters.start_from(riak_plan, ['node1.run']) == {'node1.run', 'hosts_file1.run', 'riak_service1.run'}


def test_riak_end_hosts_file1(riak_plan):
    assert filters.end_at(riak_plan, ['hosts_file1.run']) == {'node1.run', 'hosts_file1.run'}


def test_start_at_two_nodes(riak_plan):
    assert filters.start_from(riak_plan, ['node1.run', 'node2.run']) == \
        {'hosts_file1.run', 'riak_service2.run', 'riak_service2.join',
         'hosts_file2.run', 'node2.run', 'riak_service1.run', 'node1.run'}


def test_initial_from_node1_traverse(riak_plan):
    filters.filter(riak_plan, start=['node1.run'])
    pending = {n for n in riak_plan if riak_plan.node[n]['status'] == states.PENDING.name}
    assert pending == {'hosts_file1.run', 'riak_service1.run', 'node1.run'}


def test_second_from_node2_with_node1_walked(riak_plan):
    success = {'hosts_file1.run', 'riak_service1.run', 'node1.run'}
    for n in success:
        riak_plan.node[n]['status'] = states.SUCCESS.name
    filters.filter(riak_plan, start=['node2.run'])
    pending = {n for n in riak_plan if riak_plan.node[n]['status'] == states.PENDING.name}
    assert pending == {'hosts_file2.run', 'riak_service2.run',
                       'node2.run', 'riak_service2.join'}


def test_end_joins(riak_plan):
    filters.filter(
        riak_plan,
        start=['node1.run', 'node2.run', 'node3.run'],
        end=['riak_service2.join', 'riak_service3.join'])
    skipped = {n for n in riak_plan if riak_plan.node[n]['status'] == states.SKIPPED.name}

    assert skipped == {'riak_service1.commit'}
