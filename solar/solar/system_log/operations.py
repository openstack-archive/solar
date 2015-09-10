#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

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
