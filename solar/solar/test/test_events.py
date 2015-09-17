# -*- coding: utf-8 -*-
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

from solar.events import api as evapi

from .base import BaseResourceTest


@fixture
def events_example():
    return [
        evapi.Dep('e1', 'run', 'success', 'e2', 'run'),
        evapi.Dep('e1', 'run', 'success', 'e3', 'run'),
        evapi.Dep('e1', 'run', 'success', 'e4', 'run'),
    ]


def test_add_events(events_example):
    evapi.add_events('e1', events_example)
    assert set(evapi.all_events('e1')) == set(events_example)


def test_set_events(events_example):
    partial = events_example[:2]
    evapi.add_events('e1', events_example[:2])
    evapi.set_events('e1', events_example[2:])
    assert evapi.all_events('e1') == events_example[2:]


def test_remove_events(events_example):
    to_be_removed = events_example[2]
    evapi.add_events('e1', events_example)
    evapi.remove_event(to_be_removed)
    assert to_be_removed not in evapi.all_events('e1')


def test_single_event(events_example):
    evapi.add_events('e1', events_example[:2])
    evapi.add_event(events_example[2])
    assert set(evapi.all_events('e1')) == set(events_example)


@fixture
def nova_deps():
    rst = [
        evapi.Dep('nova', 'run', 'success', 'nova_api', 'run'),
        evapi.Dep('nova', 'update', 'success', 'nova_api', 'update'),
        evapi.React('nova', 'update', 'success', 'nova_api', 'update')
    ]
    return {'nova': rst}


def test_nova_api_run_after_nova(nova_deps):
    changed = ['nova', 'nova_api']
    changes_graph = nx.DiGraph()
    changes_graph.add_node('nova.run')
    changes_graph.add_node('nova_api.run')
    evapi.build_edges(changed, changes_graph, nova_deps)

    assert changes_graph.successors('nova.run') == ['nova_api.run']


def test_nova_api_react_on_update(nova_deps):
    """Test that nova_api:update will be called even if there is no changes
    in nova_api
    """
    changed = ['nova']
    changes_graph = nx.DiGraph()
    changes_graph.add_node('nova.update')
    evapi.build_edges(changed, changes_graph, nova_deps)

    assert changes_graph.successors('nova.update') == ['nova_api.update']


@fixture
def rmq_deps():
    """Example of a case when defaults are not good enough.
    For example we need to run some stuff on first node before two others.
    """
    # NOTE(dshulyak) is it possible to put this create/join logic into
    # puppet manifest? So that rmq_cluster.2 before joining will check if
    # cluster already exists?
    return {
        'rmq.1': [evapi.Dep('rmq.1', 'run', 'success', 'rmq_cluster.1', 'create')],
        'rmq.2': [evapi.Dep('rmq.2', 'run', 'success', 'rmq_cluster.2', 'join')],
        'rmq.3': [evapi.Dep('rmq.3', 'run', 'success', 'rmq_cluster.3', 'join')],
        'rmq_cluster.1': [
            evapi.Dep('rmq_cluster.1', 'create', 'success', 'rmq_cluster.2', 'join'),
            evapi.Dep('rmq_cluster.1', 'create', 'success', 'rmq_cluster.3', 'join')]}


def test_rmq(rmq_deps):
    changed = ['rmq.1', 'rmq.2', 'rmq.3', 'rmq_cluster.1', 'rmq_cluster.2', 'rmq_cluster.3']
    changes_graph = nx.DiGraph()
    changes_graph.add_node('rmq.1.run')
    changes_graph.add_node('rmq.2.run')
    changes_graph.add_node('rmq.3.run')
    changes_graph.add_node('rmq_cluster.1.create')
    changes_graph.add_node('rmq_cluster.2.join')
    changes_graph.add_node('rmq_cluster.3.join')
    evapi.build_edges(changed, changes_graph, rmq_deps)

    assert set(changes_graph.successors('rmq_cluster.1.create')) == {
        'rmq_cluster.2.join', 'rmq_cluster.3.join'}


def test_riak():

    events = {
        'riak_service1': [evapi.React('riak_service1', 'run', 'success', 'riak_service2', 'join'),
                          evapi.React('riak_service1', 'run', 'success', 'riak_service3', 'join')],
        'riak_service3': [evapi.React('riak_service3', 'join', 'success', 'riak_service1', 'commit')],
        'riak_service2': [evapi.React('riak_service2', 'join', 'success', 'riak_service1', 'commit')],

    }
    changed = ['riak_service1']
    changes_graph = nx.DiGraph()
    changes_graph.add_node('riak_service1.run')
    evapi.build_edges(changed, changes_graph, events)
    assert nx.topological_sort(changes_graph) == [
        'riak_service1.run', 'riak_service2.join', 'riak_service3.join', 'riak_service1.commit']
