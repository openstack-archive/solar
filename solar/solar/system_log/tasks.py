

from solar.orchestration.runner import app
from solar.system_log.operations import set_error, move_to_commited

__all__ = ['error_logitem', 'commit_logitem']


@app.task
def error_logitem(task_uuid):
    return set_error(task_uuid.rsplit(':', 1)[-1])


@app.task
def commit_logitem(task_uuid):
    return move_to_commited(task_uuid.rsplit(':', 1)[-1])
