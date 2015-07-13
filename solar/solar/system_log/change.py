

from dictdiffer import diff, patch, revert
import networkx as nx

from solar.core.log import log
from solar.core import signals
from solar.core import resource
from solar import utils
from solar.interfaces.db import get_db
from solar.core import actions
from solar.system_log import data

db = get_db()


def guess_action(from_, to):
    # NOTE(dshulyak) imo the way to solve this - is dsl for orchestration,
    # something where this action will be excplicitly specified
    if not from_:
        return 'run'
    elif not to:
        return 'remove'
    else:
        return 'update'


def connections(res, graph):
    result = []
    for pred in graph.predecessors(res.name):
        for num, edge in graph.get_edge_data(pred, res.name).items():
            if 'label' in edge:
                if ':' in edge['label']:
                    parent, child = edge['label'].split(':')
                    mapping = [parent, child]
                else:
                    mapping = [edge['label'], edge['label']]
            else:
                mapping = None
            result.append([pred, res.name, mapping])
    return result


def to_dict(resource, graph):
    res = resource.to_dict()
    res['connections'] = connections(resource, graph)
    return res


def create_diff(staged, commited):
    if 'connections' in commited:
        commited['connections'].sort()
        staged['connections'].sort()
    if 'tags' in commited:
        commited['tags'].sort()
        staged['tags'].sort()

    return list(diff(commited, staged))


def _stage_changes(staged_resources, conn_graph,
                   commited_resources, staged_log):

    try:
        srt = nx.topological_sort(conn_graph)
    except:
        for cycle in nx.simple_cycles(conn_graph):
            log.debug('CYCLE: %s', cycle)
        raise

    for res_uid in srt:
        commited_data = commited_resources.get(res_uid, {})
        staged_data = staged_resources.get(res_uid, {})

        df = create_diff(staged_data, commited_data)

        if df:
            log_item = data.LogItem(
                utils.generate_uuid(),
                res_uid,
                df,
                guess_action(commited_data, staged_data))
            staged_log.append(log_item)
    return staged_log


def stage_changes():
    conn_graph = signals.detailed_connection_graph()
    staged = {r.name: to_dict(r, conn_graph)
              for r in resource.load_all().values()}
    commited = data.CD()
    log = data.SL()
    log.clean()
    return _stage_changes(staged, conn_graph, commited, log)
