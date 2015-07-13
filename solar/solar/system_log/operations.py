

from solar.system_log import data


def set_error(task_uuid, *args, **kwargs):
    sl = data.SL()
    item = sl.get(task_uuid)
    if item:
        item.state = data.STATES.error
        sl.update(task_uuid, item)


def move_to_commited(task_uuid, *args, **kwargs):
    sl = data.SL()
    item = sl.get(task_uuid)
    if item:
        sl.rem(task_uuid)
        cl = data.CL()
        item.state = data.STATES.success
        cl.append(item)
