

from solar import state
from solar.core import signals
from solar.core import resource
from solar import utils
from solar.interfaces.db import get_db
from solar.core import actions

db = get_db()

from dictdiffer import diff, patch, revert
import networkx as nx
import subprocess


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
    return {'uid': resource.name,
            'tags': resource.tags,
            'args': resource.args_dict(),
            'connections': connections(resource, graph)}


def stage_changes():
    resources = resource.load_all()
    conn_graph = signals.detailed_connection_graph()

    commited = state.CD()
    log = state.SL()
    action = None

    try:
        srt = nx.topological_sort(conn_graph)
    except:
        for cycle in nx.simple_cycles(conn_graph):
            print 'CYCLE: %s' % cycle
        raise

    for res_uid in srt:
        commited_data = commited.get(res_uid, {})
        staged_data = to_dict(resources[res_uid], conn_graph)

        if 'connections' in commited_data:
            commited_data['connections'].sort()
            staged_data['connections'].sort()
        if 'tags' in commited_data:
            commited_data['tags'].sort()
            staged_data['tags'].sort()

        df = list(diff(commited_data, staged_data))
        if df:

            log_item = state.LogItem(
                utils.generate_uuid(),
                res_uid,
                df,
                guess_action(commited_data, staged_data))
            log.add(log_item)
    return log


def execute(res, action):
    try:
        actions.resource_action(res, action)
        return state.STATES.success
    except subprocess.CalledProcessError:
        return state.STATES.error


def commit(li, resources):
    commited = state.CD()
    history = state.CL()
    staged = state.SL()

    staged_res = resources[li.res]

    staged_data = patch(li.diff, commited.get(li.res, {}))

    # TODO(dshulyak) think about this hack for update
    if li.action == 'update':
        commited_res = resource.Resource(
            staged_res.name,
            staged_res.metadata,
            commited[li.res]['args'],
            commited[li.res]['tags'])
        result_state = execute(commited_res, 'remove')

        if result_state is state.STATES.success:
            result_state = execute(staged_res, 'run')
    else:
        result_state = execute(staged_res, li.action)

    # resource_action return None in case there is no actions
    result_state = result_state or state.STATES.success

    commited[li.res] = staged_data
    li.state = result_state

    history.add(li)

    if result_state is state.STATES.error:
        raise Exception('Failed')


def commit_one():
    staged = state.SL()
    resources = resource.load_all()
    commit(staged.popleft(), resources)


def commit_changes():
    # just shortcut to test stuff
    commited = state.CD()
    history = state.CL()
    staged = state.SL()
    resources = resource.load_all()

    while staged:
        commit(staged.popleft(), resources)


def rollback(log_item):
    log = state.SL()

    resources = resource.load_all()
    commited = state.CD()[log_item.res]

    staged = revert(log_item.diff, commited)

    for e, r, mapping in commited.get('connections', ()):
        signals.disconnect(resources[e], resources[r])

    for e, r, mapping in staged.get('connections', ()):
        signals.connect(resources[e], resources[r], dict([mapping]))

    df = list(diff(commited, staged))

    log_item = state.LogItem(
        utils.generate_uuid(),
        log_item.res, df, guess_action(commited, staged))
    log.add(log_item)

    res = resource.load(log_item.res)
    res.update(staged.get('args', {}))
    #res.save()

    return log


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


