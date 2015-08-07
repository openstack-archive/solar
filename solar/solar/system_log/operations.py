

from solar.system_log import data
from dictdiffer import patch


def set_error(log_action, *args, **kwargs):
    sl = data.SL()
    item = sl.get(log_action)
    if item:
        item.state = data.STATES.error
        sl.update(item)


def move_to_commited(log_action, *args, **kwargs):
    sl = data.SL()
    item = sl.pop(log_action)
    if item:
        commited = data.CD()
        staged_data = patch(item.diff, commited.get(item.log_action, {}))
        cl = data.CL()
        item.state = data.STATES.success
        cl.append(item)
        commited[item.res] = staged_data
