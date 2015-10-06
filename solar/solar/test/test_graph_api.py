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
from copy import deepcopy

from pytest import fixture

from solar.orchestration import graph
from solar.orchestration.traversal import states


@fixture
def simple():
    simple_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'orch_fixtures',
        'simple.yaml')
    return graph.create_plan(simple_path)


def test_simple_plan_created_and_loaded(simple):
    plan = graph.get_plan(simple.graph['uid'])
    assert set(plan.nodes()) == {'just_fail', 'echo_stuff'}


def test_update_plan_with_new_node(simple):
    new = deepcopy(simple)
    new.add_node('one_more', {})
    graph.update_plan_from_graph(new, simple)
    updated = graph.get_plan(new.graph['uid'])
    assert set(updated.nodes()) == {'one_more', 'just_fail', 'echo_stuff'}


def test_status_preserved_on_update(simple):
    new = deepcopy(simple)
    task_under_test = 'echo_stuff'

    assert new.node[task_under_test]['status'] == states.PENDING.name

    simple.node[task_under_test]['status'] = states.SUCCESS.name
    graph.update_plan_from_graph(new, simple)

    updated = graph.get_plan(new.graph['uid'])
    assert new.node[task_under_test]['status'] == states.SUCCESS.name


def test_reset_all_states(simple):
    for n in simple:
        simple.node[n]['status'] == states.ERROR.name
    graph.reset(simple)

    for n in simple:
        assert simple.node[n]['status'] == states.PENDING.name


def test_reset_only_provided(simple):
    simple.node['just_fail']['status'] = states.ERROR.name
    simple.node['echo_stuff']['status'] = states.SUCCESS.name

    graph.reset(simple, [states.ERROR.name])

    assert simple.node['just_fail']['status'] == states.PENDING.name
    assert simple.node['echo_stuff']['status'] == states.SUCCESS.name


def test_wait_finish(simple):
    for n in simple:
        simple.node[n]['status'] = states.SUCCESS.name
    graph.save_graph(simple)

    assert list(graph.wait_finish(simple.graph['uid'], 10)) == [(0, 2)]


def test_several_updates(simple):
    simple.node['just_fail']['status'] = states.ERROR.name
    graph.save_graph(simple)

    assert next(graph.wait_finish(simple.graph['uid'], 10)) == (1, 2)

    simple.node['echo_stuff']['status'] = states.ERROR.name
    graph.save_graph(simple)

    assert next(graph.wait_finish(simple.graph['uid'], 10)) == (0, 2)
