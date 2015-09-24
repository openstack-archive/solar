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

import mock

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
        res.name, action, change.create_diff(commit, previous), [],
        base_path=res.base_path)
    log.append(logitem)
    resource_obj.update(commit)
    operations.move_to_commited(logitem.log_action)

    assert logitem.diff == [('change', 'a', ('9', '10'))]
    assert resource_obj.args == commit

    change.revert(logitem.uid)
    assert resource_obj.args == previous


def test_revert_removal():
    res = orm.DBResource(id='test1', name='test1', base_path='x')
    res.save()
    res.add_input('a', 'str', '9')
    res.delete()
    commited = orm.DBCommitedState.get_or_create('test1')
    commited.inputs = {'a': '9'}
    commited.save()

    logitem =change.create_logitem(
        res.name, 'remove', change.create_diff({}, {'a': '9'}), [],
        base_path=res.base_path)
    log = data.SL()
    log.append(logitem)
    operations.move_to_commited(logitem.log_action)

    resources = orm.DBResource.load_all()

    assert resources == []
    assert logitem.diff == [('remove', '', [('a', '9')])]

    with mock.patch.object(resource, 'read_meta') as mread:
        mread.return_value = {'input': {'a': {'schema': 'str!'}}}
        change.revert(logitem.uid)
    resource_obj = resource.load('test1')
    assert resource_obj.args == {'a': '9'}


def test_revert_create():
    res = orm.DBResource(id='test1', name='test1', base_path='x')
    res.save()
    res.add_input('a', 'str', '9')

    logitem =change.create_logitem(
        res.name, 'run', change.create_diff({'a': '9'}, {}), [],
        base_path=res.base_path)
    log = data.SL()
    log.append(logitem)
    assert logitem.diff == [('add', '', [('a', '9')])]

    operations.move_to_commited(logitem.log_action)
    commited = orm.DBCommitedState.load('test1')
    assert commited.inputs == {'a': '9'}

    change.revert(logitem.uid)

    resources = orm.DBResource.load_all()
    assert resources == []
