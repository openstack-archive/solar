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

from .traversal import VISITED, states


def get_dfs_postorder_subgraph(dg, nodes):
    result = set()
    for node in nodes:
        result.update(nx.dfs_postorder_nodes(dg, source=node))
    return dg.subgraph(result)


def end_at(dg, nodes):
    """Returns subgraph that will guarantee that predecessors are visited
    dg - directed graph
    nodes - iterable with node names
    """
    return set(get_dfs_postorder_subgraph(dg.reverse(), nodes).nodes())


def start_from(dg, start_nodes):
    """Guarantee that all paths starting from specific *nodes* will be visited
    """
    visited = {n for n in dg if dg.node[n].get('status') in VISITED}

    # sorting nodes in topological order will guarantee that all predecessors
    # of current node were already walked, when current going to be considered
    for node in nx.topological_sort(dg):
        preds = dg.predecessors(node)
        if not preds and node in start_nodes:
            visited.add(node)

        if preds:
            for pred in preds:
                if pred not in visited:
                    break
            else:
                visited.add(node)
    return visited


def validate(dg, start_nodes, end_nodes, err_msgs):
    error_msgs = err_msgs[:]
    not_in_the_graph_msg = 'Node {} is not present in graph {}'
    for n in start_nodes:
        if n not in dg:
            error_msgs.append(not_in_the_graph_msg.format(n, dg.graph['uid']))
    for n in end_nodes:
        if n not in dg:
            if start_nodes:
                error_msgs.append(
                    'No path from {} to {}'.format(start_nodes, n))
            else:
                error_msgs.append(
                    not_in_the_graph_msg.format(n, dg.graph['uid']))
    return error_msgs


def filter(dg, start=None, end=None, tasks=(), skip_with=states.SKIPPED.name):
    """
    TODO(dshulyak) skip_with should also support NOOP, which will instead
    of blocking task, and its successors, should mark task as visited

    :param skip_with: SKIPPED or NOOP
    """
    error_msgs = []
    subpath = dg.nodes()
    if tasks:
        subpath = tasks
    else:

        subgraph = dg
        if start:
            error_msgs = validate(subgraph, start, [], error_msgs)
            if error_msgs:
                return error_msgs

            subpath = start_from(subgraph, start)
            subgraph = dg.subgraph(subpath)
        if end:
            error_msgs = validate(subgraph, start, end, error_msgs)
            if error_msgs:
                return error_msgs

            subpath = end_at(subgraph, end)

    for node in dg:
        if node not in subpath:
            dg.node[node]['status'] = skip_with
    return None
