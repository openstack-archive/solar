

from solar.orchestration.runner import app


# TODO(dshulyak) some tasks should be evaluated even if not all predecessors
# succeded, how to identify this?
# - add ignor_error on edge
# - add ignore_predecessor_errors on task in consideration
# - make fault_tolerance not a task but a policy for all tasks
def traverse(dg, control_tasks=()):
    """
    1. Node should be visited only when all predecessors already visited
    2. Visited nodes should have any state except PENDING, INPROGRESS, for now
    is SUCCESS or ERROR, but it can be extended
    3. If node is INPROGRESS it should not be visited once again
    """
    visited = set()
    for node in dg:
        data = dg.node[node]
        if data['status'] not in ('PENDING', 'INPROGRESS', 'SKIPPED'):
            visited.add(node)

    for node in dg:
        data = dg.node[node]

        if node in visited:
            continue
        elif data['status'] in ('INPROGRESS', 'SKIPPED'):
            continue

        predecessors = set(dg.predecessors(node))

        if predecessors <= visited:
            task_id = '{}:{}'.format(dg.graph['uid'], node)

            task_name = '{}.{}'.format(__name__, data['type'])
            task = app.tasks[task_name]

            if all_success(dg, predecessors) or task in control_tasks:
                dg.node[node]['status'] = 'INPROGRESS'
                for t in generate_task(task, dg, data, task_id):
                    yield t


def generate_task(task, dg, data, task_id):

    subtask = task.subtask(
        data['args'], task_id=task_id,
        time_limit=data.get('time_limit', None),
        soft_time_limit=data.get('soft_time_limit', None))

    if data.get('target', None):
        subtask.set(queue=data['target'])

    yield subtask


def all_success(dg, nodes):
    return all((dg.node[n]['status'] == 'SUCCESS' for n in nodes))
