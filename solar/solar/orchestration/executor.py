
from solar.orchestration.runner import app
from celery import group


def celery_executor(dg, tasks, control_tasks=()):
    to_execute = []

    for task_name in tasks:

        # task_id needs to be unique, so for each plan we will use
        # generated uid of this plan and task_name
        task_id = '{}:{}'.format(dg.graph['uid'], task_name)
        task = app.tasks[dg.node[task_name]['type']]

        if all_success(dg, dg.predecessors(task_name)) or task_name in control_tasks:
            dg.node[task_name]['status'] = 'INPROGRESS'
            for t in generate_task(task, dg.node[task_name], task_id):
                to_execute.append(t)
    return group(to_execute)


def generate_task(task, data, task_id):

    subtask = task.subtask(
        data['args'], task_id=task_id,
        time_limit=data.get('time_limit', None),
        soft_time_limit=data.get('soft_time_limit', None))

    if data.get('target', None):
        subtask.set(queue=data['target'])

    yield subtask


def all_success(dg, nodes):
    return all((dg.node[n]['status'] == 'SUCCESS' for n in nodes))
