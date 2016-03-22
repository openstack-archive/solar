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

import subprocess

import networkx as nx

STATE_COLORS = {
    'PENDING': 'cyan',
    'ERROR': 'red',
    'SUCCESS': 'green',
    'INPROGRESS': 'yellow',
    'SKIPPED': 'blue',
    'NOOP': 'black',
    'ERROR_RETRY': 'red',
    'POLICY_BLOCKED': 'cyan'}


def write_graph(plan):
    """Writes graph to dot then to svg

    :param plan: networkx Graph object
    """
    simplified = nx.MultiDiGraph()

    for n in plan.nodes():
        simplified.add_node(n.name)
        simplified.node[n.name]['color'] = STATE_COLORS[n.status]
        simplified.add_edges_from(
            [(n.name, s.name) for s in plan.successors(n)])

    nx.nx_pydot.write_dot(
        simplified, '{name}.dot'.format(name=plan.graph['name']))
    subprocess.call(
        'tred {name}.dot | dot -Tsvg -o {name}.svg'.format(
            name=plan.graph['name']),
        shell=True)
