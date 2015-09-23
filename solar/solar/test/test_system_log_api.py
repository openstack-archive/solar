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


from pytest import fixture
from solar.system_log import change
from solar.system_log import data
from solar.system_log import operations
from solar.core.resource import resource
from solar.interfaces import orm


def test_revert_update():
    commit = {'a': '10'}
    previous = {'a': '9'}
    res = orm.DBResource(id='test1', name='test1', base_path='x')
    res.save()
    res.add_input('a', 'str', '9')
    action = 'update'

    resource_obj = resource.load(res.name)

    assert resource_obj.args == previous

    log = data.SL()
    logitem =change.create_logitem(
        res.name, action, change.create_diff(commit, previous))
    log.append(logitem)
    resource_obj.update(commit)
    operations.move_to_commited(logitem.log_action)

    assert resource_obj.args == commit

    change.revert(logitem.uid)
    assert resource_obj.args == previous
