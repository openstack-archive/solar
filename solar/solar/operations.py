

from solar import state
from solar.core.log import log
from solar.core import signals
from solar.core import resource
from solar import utils
from solar.interfaces.db import get_db
from solar.core import actions

db = get_db()

from dictdiffer import diff, patch, revert
from fabric import api as fabric_api
import networkx as nx


def guess_action(from_, to):
    # TODO(dshulyak) it should be more flexible
    if not from_:
        return 'run'
    elif not to:
        return 'remove'
    else:
        # it should be update
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

    action = None

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

            log_item = state.LogItem(
                utils.generate_uuid(),
                res_uid,
                df,
                guess_action(commited_data, staged_data))
            staged_log.append(log_item)
    return staged_log


def stage_changes():
    conn_graph = signals.detailed_connection_graph()
    staged = {r.name: to_dict(r, conn_graph) for r in resource.load_all().values()}
    commited = state.CD()
    log = state.SL()
    log.delete()
    return _stage_changes(staged, conn_graph, commited, log)


def execute(res, action):
    #return state.STATES.success
    try:
        actions.resource_action(res, action)
        return state.STATES.success
    except Exception as e:
        return state.STATES.error


def commit(li, resources, commited, history):

    staged_res = resources[li.res]
    staged_data = patch(li.diff, commited.get(li.res, {}))

    # TODO(dshulyak) think about this hack for update
    if li.action == 'update':
        commited_res = resource.wrap_resource(
            commited[li.res]['metadata'])
        result_state = execute(commited_res, 'remove')

        if result_state is state.STATES.success:
            result_state = execute(staged_res, 'run')
    else:
        result_state = execute(staged_res, li.action)

    # resource_action return None in case there is no actions
    result_state = result_state or state.STATES.success

    commited[li.res] = staged_data
    li.state = result_state

    history.append(li)

    if result_state is state.STATES.error:
        raise Exception('Failed')


def commit_one():
    commited = state.CD()
    history = state.CL()
    staged = state.SL()

    resources = resource.load_all()
    commit(staged.popleft(), resources, commited, history)


def commit_changes():
    # just shortcut to test stuff
    commited = state.CD()
    history = state.CL()
    staged = state.SL()
    resources = resource.load_all()

    while staged:
        commit(staged.popleft(), resources, commited, history)


def rollback(log_item):
    log = state.SL()

    resources = resource.load_all()
    commited = state.CD()[log_item.res]

    staged = revert(log_item.diff, commited)

    for e, r, mapping in commited.get('connections', ()):
        signals.disconnect(resources[e], resources[r])

    for e, r, mapping in staged.get('connections', ()):
        signals.connect(resources[e], resources[r], dict([mapping]))

    df = create_diff(staged, commited)

    log_item = state.LogItem(
        utils.generate_uuid(),
        log_item.res, df, guess_action(commited, staged))
    log.append(log_item)

    res = resource.load(log_item.res)
    res.set_args_from_dict(staged['input'])

    return log_item


def rollback_uid(uid):
    item = next(l for l in state.CL() if l.uid == uid)
    return rollback(item)


def rollback_last():
    l = state.CL().items[-1]
    return rollback(l)


def rollback_all():
    cl = state.CL()

    while cl:
        rollback(cl.pop())


