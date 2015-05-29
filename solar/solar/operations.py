

from solar import state
from solar.core import signals
from solar.core import resource

from dictdiffer import diff
import networkx as nx


def connections(res, graph):

    for pred in graph.predecessors(res.name):
        edge = graph.get_edge_edge(pred, res.name)
        if ':' in edge['label']:
            parent, child = edge['label'].split(':')
            yield pred, res.name, {parent: child}
        else:
            yield pred, res.name, {edge['label']: edge['label']}


def to_dict(resource, graph):
    return {'uid': resource.name,
            'path': resource.dest_path,
            'meta': resource.metadata,
            'tags': resource.tags,
            'args': resource.args_dict(),
            'connections': connections(resource, graph)}


def stage_changes():
    resources = resource.load_all()
    conn_graph = signals.detailed_connection_graph()

    commited = state.CD()
    log = state.SL()

    for res_uid in nx.topological_sort(conn_graph):
        commited_data = commited.get(res_uid, {})
        staged_data = to_dict(resources[res_uid], conn_graph)
        df = diff(commited_data, staged_data)

        if df:
            log_item = state.LogItem(
                utils.generate_uuid(),
                res_uid,
                df)
            log.add(log_item)
    return log

