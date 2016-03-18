#    Copyright 2016 Mirantis, Inc.
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

import mock

import networkx as nx

from solar.orchestration import graph


def test_longest_path_time_returns_0_for_empty_graph():
    g = nx.MultiDiGraph()
    assert graph.longest_path_time(g) == 0.0


def test_reset_resets_times():
    g = nx.MultiDiGraph()
    g.add_node('task1', task=mock.Mock(), status='status', errmsg='',
               start_time=1, end_time=4)
    graph.reset(g)
    assert int(g.node['task1']['start_time']) == 0


def test_subgraph_from_task(simple_plan):
    mdg = graph.subgraph_from_task(
        simple_plan.graph['uid'], 'echo_stuff')
    echo_id = '{}~{}'.format(simple_plan.graph['uid'], 'echo_stuff')
    just_fail_id = '{}~just_fail'.format(simple_plan.graph['uid'])
    assert mdg.successors(echo_id) == [just_fail_id]
