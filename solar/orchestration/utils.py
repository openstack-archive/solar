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


def write_graph(plan):
    """Writes graph to dot then to svg

    :param plan: networkx Graph object
    """
    names_only = nx.MultiDiGraph()
    names_only.add_nodes_from([n.name for n in plan.nodes()])
    names_only.add_edges_from([(n.name, s.name) for n in plan.nodes()
                               for s in plan.successors(n)])
    colors = {
        'PENDING': 'cyan',
        'ERROR': 'red',
        'SUCCESS': 'green',
        'INPROGRESS': 'yellow',
        'SKIPPED': 'blue',
        'NOOP': 'black'}

    for n in plan.nodes():
        names_only.node[n.name]['color'] = colors[n.status]

    nx.nx_pydot.write_dot(names_only,
                          '{name}.dot'.format(name=plan.graph['name']))
    subprocess.call(
        'tred {name}.dot | dot -Tsvg -o {name}.svg'.format(
            name=plan.graph['name']),
        shell=True)
