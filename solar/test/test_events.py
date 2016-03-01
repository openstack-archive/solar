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

from solar.dblayer.solar_models import Resource
from solar.events import api as evapi


@fixture
def events_example():
    return [
        evapi.Dep('e1', 'run', 'success', 'e2', 'run'),
        evapi.Dep('e1', 'run', 'success', 'e3', 'run'),
        evapi.Dep('e1', 'run', 'success', 'e4', 'run'),
    ]


def test_add_events(events_example):
    r = Resource.from_dict(dict(key='e1', name='e1', base_path='x'))
    r.save()

    evapi.add_events('e1', events_example)
    assert set(evapi.all_events('e1')) == set(events_example)


def test_remove_events(events_example):
    r = Resource.from_dict(dict(key='e1', name='e1', base_path='x'))
    r.save()
    to_be_removed = events_example[2]
    evapi.add_events('e1', events_example)
    evapi.remove_event(to_be_removed)
    assert to_be_removed not in evapi.all_events('e1')


def test_single_event(events_example):
    r = Resource.from_dict(dict(key='e1', name='e1', base_path='x'))
    r.save()
    evapi.add_events('e1', events_example[:2])
    evapi.add_event(events_example[2])
    assert set(evapi.all_events('e1')) == set(events_example)


@fixture
def nova_deps():
    for name in ['nova', 'nova_api', 'nova_sch']:
        r = Resource.from_dict(dict(key=name, name=name))
        r.inputs.add_new('location_id', '1')
        r.save()
    nova = [
        evapi.Dep('nova', 'run', 'success', 'nova_sch', 'run'),
        evapi.React('nova', 'run', 'success', 'nova_api', 'update')]
    nova_api = [
        evapi.React('nova_api', 'update', 'success', 'nova', 'reboot')]
    evapi.add_events('nova', nova)
    evapi.add_events('nova_api', nova_api)
    return {'nova': nova}


def test_nova_api(nova_deps):
    changes_graph = nx.DiGraph()
    changes_graph.add_node('nova.run')
    changes_graph.add_node('nova_sch.run')
    evapi.build_edges(changes_graph, nova_deps)

    assert set(changes_graph.successors('nova.run')) == {
        'nova_sch.run', 'nova_api.update'}
    assert changes_graph.successors('nova_api.update') == ['nova.reboot']


@fixture
def rmq_deps():
    """Example of a case when defaults are not good enough.

    For example we need to run some stuff on first node before two others.
    """
    # NOTE(dshulyak) is it possible to put this create/join logic into
    # puppet manifest? So that rmq_cluster.2 before joining will check if
    # cluster already exists?
    return {
        'rmq.1':
        [evapi.Dep('rmq.1', 'run', 'success', 'rmq_cluster.1', 'create')],
        'rmq.2':
        [evapi.Dep('rmq.2', 'run', 'success', 'rmq_cluster.2', 'join')],
        'rmq.3':
        [evapi.Dep('rmq.3', 'run', 'success', 'rmq_cluster.3', 'join')],
        'rmq_cluster.1': [
            evapi.Dep('rmq_cluster.1', 'create', 'success', 'rmq_cluster.2',
                      'join'), evapi.Dep('rmq_cluster.1', 'create', 'success',
                                         'rmq_cluster.3', 'join')
        ]
    }


def test_rmq(rmq_deps):
    changes_graph = nx.DiGraph()
    changes_graph.add_node('rmq.1.run')
    changes_graph.add_node('rmq.2.run')
    changes_graph.add_node('rmq.3.run')
    changes_graph.add_node('rmq_cluster.1.create')
    changes_graph.add_node('rmq_cluster.2.join')
    changes_graph.add_node('rmq_cluster.3.join')
    evapi.build_edges(changes_graph, rmq_deps)

    assert set(changes_graph.successors('rmq_cluster.1.create')) == {
        'rmq_cluster.2.join', 'rmq_cluster.3.join'
    }


def test_riak():

    events = {
        'riak_service1': [
            evapi.React('riak_service1', 'run', 'success', 'riak_service2',
                        'run'), evapi.React('riak_service1', 'run', 'success',
                                            'riak_service3', 'run')
        ],
        'riak_service3': [
            evapi.React('riak_service3', 'join', 'success', 'riak_service1',
                        'commit'),
            evapi.React('riak_service3', 'run', 'success', 'riak_service3',
                        'join')
        ],
        'riak_service2': [
            evapi.React('riak_service2', 'run', 'success', 'riak_service2',
                        'join'),
            evapi.React('riak_service2', 'join', 'success', 'riak_service1',
                        'commit')
        ],
    }
    for name in events:
        res = Resource.from_dict({'key': name, 'name': name})
        res.save()
        res.inputs.add_new('location_id', '1')
        evapi.add_events(name, events[name])

    changes_graph = nx.MultiDiGraph()
    changes_graph.add_node('riak_service1.run')
    evapi.build_edges(changes_graph, events)
    assert set(changes_graph.predecessors('riak_service1.commit')) == {
        'riak_service2.join', 'riak_service3.join'
    }
