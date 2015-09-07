
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


def filter(dg, start=None, end=None, tasks=(), skip_with=states.SKIPPED.name):
    """
    TODO(dshulyak) skip_with should also support NOOP, which will instead
    of blocking task, and its successors, should mark task as visited

    :param skip_with: SKIPPED or NOOP
    """

    if tasks:
        subpath = tasks
    else:

        subgraph = dg
        if start:
            subpath = start_from(subgraph, start)
            subgraph = dg.subgraph(subpath)
        if end:
            subpath = end_at(subgraph, end)

    for node in dg:
        if node not in subpath:
            dg.node[node]['status'] = skip_with
    return dg
