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
    colors = {
        'PENDING': 'cyan',
        'ERROR': 'red',
        'SUCCESS': 'green',
        'INPROGRESS': 'yellow',
        'SKIPPED': 'blue'}

    for n in plan:
        color = colors[plan.node[n]['status']]
        plan.node[n]['color'] = color

    nx.write_dot(plan, '{name}.dot'.format(name=plan.graph['name']))
    subprocess.call(
        'tred {name}.dot | dot -Tsvg -o {name}.svg'.format(
            name=plan.graph['name']),
        shell=True)
