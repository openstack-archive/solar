
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


def start_from(dg, nodes):
    """Guarantee that all paths starting from specific *nodes* will be visited
    """
    return get_dfs_postorder_subgraph(dg, nodes)


def filter_tasks(dg, nodes):
    return dg.subgraph(nodes)


def one_task(dg, node):
    return filter_tasks(dg, [node])


def traverse(dg, start=None, end=None):
    if start:
        dg = start_from(dg, start)
    if end:
        dg = end_at(dg, end)
    return dg


def exclude_paths(dg, nodes):
    """Node should be excluded from the path only if all predecessors are already
    on this path, otherwise it should not be excluded

    This is straightforward way of doing this - should be optimized
    """
    exclude_nodes = set(nodes)
    stack = nodes
    all_nodes = set(dg.nodes())
    while stack:
        current = stack.pop()
        if current in exclude_nodes:
            stack.extend(dg.successors(current))
        elif set(dg.predecessors(current)) <= exclude_nodes:
            exclude_nodes.add(current)
    return dg.subgraph(all_nodes - exclude_nodes)
