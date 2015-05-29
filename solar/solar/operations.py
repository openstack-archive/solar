

from solar import state
from solar.core import signals
from solar.core import resource
from solar import utils

from dictdiffer import diff, patch
import networkx as nx


def connections(res, graph):
    result = []
    for pred in graph.predecessors(res.name):
        edge = graph.get_edge_data(pred, res.name)
        if 'label' in edge:
            if ':' in edge['label']:
                parent, child = edge['label'].split(':')
                mapping = {parent: child}
            else:
                mapping = {edge['label']: edge['label']}
        else:
            mapping = None
        result.append((pred, res.name, mapping))
    return result


def to_dict(resource, graph):
    return {'uid': resource.name,
            'path': resource.base_dir,
            'tags': resource.tags,
            'args': resource.args_dict(),
            'connections': connections(resource, graph)}


def stage_changes(path):
    resources = resource.load_all(path)
    conn_graph = signals.detailed_connection_graph()

    commited = state.CD()
    log = state.SL()

    for res_uid in nx.topological_sort(conn_graph):
        commited_data = commited.get(res_uid, {})
        staged_data = to_dict(resources[res_uid], conn_graph)
        df = list(diff(commited_data, staged_data))

        if df:
            log_item = state.LogItem(
                utils.generate_uuid(),
                res_uid,
                df)
            log.add(log_item)
    return log


def commit_changes():
    # just shortcut to test stuff
    commited = state.CD()
    history = state.CL()
    staged = state.SL()

    while staged:
        l = staged.popleft()

        commited[l.res] = patch(commited.get(l.res, {}), l.diff)
        l.state = state.STATES.success
        history.add(l)
