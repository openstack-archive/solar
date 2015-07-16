

from solar.system_log import data
from dictdiffer import patch


def set_error(task_uuid, *args, **kwargs):
    sl = data.SL()
    item = sl.get(task_uuid)
    if item:
        item.state = data.STATES.error
        sl.update(item)


def move_to_commited(task_uuid, *args, **kwargs):
    sl = data.SL()
    item = sl.pop(task_uuid)
    if item:
        commited = data.CD()
        staged_data = patch(item.diff, commited.get(item.res, {}))
        cl = data.CL()
        item.state = data.STATES.success
        cl.append(item)
        commited[item.res] = staged_data
