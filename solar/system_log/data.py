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


from solar.dblayer.solar_models import LogItem


def SL():
    rst = LogItem.composite.filter({'log': 'staged'})
    return LogItem.multi_get(rst)


def CL():
    rst = LogItem.composite.filter({'log': 'history'})
    return LogItem.multi_get(rst)


def compact(logitem):
    return 'log task={} uid={}'.format(logitem.log_action, logitem.uid)


def details(diff):
    rst = []
    for type_, val, change in diff:
        if type_ == 'add':
            for key, val in change:
                rst.append('++ {}: {}'.format(key, val))
        elif type_ == 'change':
            rst.append('-+ {}: {} >> {}'.format(
                unwrap_change_val(val), change[0], change[1]))
        elif type_ == 'remove':
            for key, val in change:
                rst.append('-- {}: {}'.format(key, val))
    return rst


def unwrap_add(it):
    if isinstance(it, dict):
        if it['emitter']:
            return '{}::{}'.format(it['emitter'], it['value'])
        return it['value']
    elif isinstance(it, list):
        return [unwrap_add(i) for i in it]
    else:
        return it[1]


def unwrap_change_val(val):
    if isinstance(val, list):
        return '{}:[{}] '.format(val[0], val[1])
    else:
        return val
