
import networkx as nx


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
    return get_dfs_postorder_subgraph(dg.reverse(), nodes)


def start_from(dg, start_nodes, topo):
    """Guarantee that all paths starting from specific *nodes* will be visited
    """
    visited = []

    for node in topo:
        preds = dg.predecessors(node)
        if not preds and node in start_nodes:
            visited.append(node)


        if preds:
            for pred in preds:
                if pred not in visited:
                    break
            else:
                visited.append(node)
    return visited


def filter_tasks(dg, nodes):
    return dg.subgraph(nodes)


def one_task(dg, node):
    return filter_tasks(dg, [node])


def traverse(dg, start=None, end=None, tasks=(), skip_with='SKIPPED'):
    """
    TODO(dshulyak) skip_with should also support NOOP, which will instead
    of blocking task, and its successors, should mark task as visited

    :param skip_with: SKIPPED or NOOP
    """

    if tasks:
        subpath = tasks
    else:
        topo = nx.topological_sort(dg)
        subgraph = dg
        if start:
            subpath = start_from(subgraph, start, topo)
            subgraph = dg.subgraph(subpath)
        if end:
            subpath = end_at(subgraph, end)

    for node in dg:
        if node not in subpath:
            dg.node[node]['status'] = skip_with
    return dg
