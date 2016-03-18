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

from solar.orchestration.traversal import states
from solar.orchestration.traversal import VISITED


def make_full_name(graph, name):
    return '{}~{}'.format(graph.graph['uid'], name)


def get_tasks_from_names(graph, names):
    return [t for t in graph.nodes() if t.name in names]


def get_dfs_postorder_subgraph(dg, nodes):
    result = set()
    for node in nodes:
        result.update(nx.dfs_postorder_nodes(dg, source=node))
    return {n for n in dg if n in result}


def end_at(dg, nodes):
    """Returns subgraph that will guarantee that predecessors are visited

    dg - directed graph
    nodes - iterable with node names
    """
    return get_dfs_postorder_subgraph(dg.reverse(copy=False), nodes)


def start_from(dg, start_nodes):
    """Ensures that all paths starting from specific *nodes* will be visited"""
    visited = {t for t in dg if t.status in VISITED}

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
        if make_full_name(dg, n) not in dg:
            error_msgs.append(not_in_the_graph_msg.format(n, dg.graph['uid']))
    for n in end_nodes:
        if make_full_name(dg, n) not in dg:
            if start_nodes:
                error_msgs.append(
                    'No path from {} to {}'.format(start_nodes, n))
            else:
                error_msgs.append(
                    not_in_the_graph_msg.format(n, dg.graph['uid']))
    return error_msgs


def filter(dg, start=None, end=None, tasks=(), skip_with=states.SKIPPED.name):
    """Filters a graph

    TODO(dshulyak) skip_with should also support NOOP, which will instead
    of blocking task, and its successors, should mark task as visited

    :param skip_with: SKIPPED or NOOP
    """
    error_msgs = []
    subpath = dg.nodes()
    if tasks:
        subpath = get_tasks_from_names(dg, tasks)
    else:
        subgraph = dg
        if start:
            error_msgs = validate(subgraph, start, [], error_msgs)
            if error_msgs:
                return error_msgs
            subpath = start_from(subgraph, get_tasks_from_names(dg, start))
            subgraph = dg.subgraph(subpath)
        if end:
            error_msgs = validate(subgraph, start, end, error_msgs)
            if error_msgs:
                return error_msgs
            subpath = end_at(subgraph, get_tasks_from_names(dg, end))

    for task in dg.nodes():
        if task not in subpath:
            task.status = skip_with
    return None
