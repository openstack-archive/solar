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
from pytest import mark

from solar.core.resource import resource
from solar.core.resource import RESOURCE_STATE
from solar.core import signals
from solar.dblayer.model import ModelMeta
from solar.dblayer.solar_models import CommitedResource
from solar.dblayer.solar_models import Resource as DBResource
from solar.system_log import change
from solar.system_log import data
from solar.system_log import operations


def test_revert_update():
    commit = {'a': '10'}
    previous = {'a': '9'}
    res = DBResource.from_dict('test1',
                               {'name': 'test1',
                                'base_path': 'x',
                                'meta_inputs': {'a': {'value': None,
                                                      'schema': 'str'}}})
    res.save()
    action = 'update'
    res.inputs['a'] = '9'
    resource_obj = resource.load(res.name)

    assert resource_obj.args == previous

    log = data.SL()
    logitem = change.create_logitem(res.name,
                                    action,
                                    change.create_diff(commit, previous),
                                    [],
                                    base_path=res.base_path)
    log.append(logitem)
    resource_obj.update(commit)
    operations.move_to_commited(logitem.log_action)

    assert logitem.diff == [('change', 'a', ('9', '10'))]
    assert resource_obj.args == commit

    change.revert(logitem.uid)
    assert resource_obj.args == previous


def test_revert_update_connected():
    res1 = DBResource.from_dict('test1',
                                {'name': 'test1',
                                 'base_path': 'x',
                                 'state': RESOURCE_STATE.created.name,
                                 'meta_inputs': {'a': {'value': None,
                                                       'schema': 'str'}}})
    res1.inputs['a'] = '9'
    res1.save_lazy()

    res2 = DBResource.from_dict('test2',
                                {'name': 'test2',
                                 'base_path': 'x',
                                 'state': RESOURCE_STATE.created.name,
                                 'meta_inputs': {'a': {'value': None,
                                                       'schema': 'str'}}})
    res2.inputs['a'] = ''
    res2.save_lazy()

    res3 = DBResource.from_dict('test3',
                                {'name': 'test3',
                                 'base_path': 'x',
                                 'state': RESOURCE_STATE.created.name,
                                 'meta_inputs': {'a': {'value': None,
                                                       'schema': 'str'}}})
    res3.inputs['a'] = ''
    res3.save_lazy()

    res1 = resource.load('test1')
    res2 = resource.load('test2')
    res3 = resource.load('test3')
    res1.connect(res2)
    res2.connect(res3)
    ModelMeta.save_all_lazy()

    staged_log = change.stage_changes()
    assert len(staged_log) == 3

    for item in staged_log:
        assert item.action == 'run'
        operations.move_to_commited(item.log_action)
    assert len(change.stage_changes()) == 0

    res1.disconnect(res2)
    staged_log = change.stage_changes()
    assert len(staged_log) == 2
    to_revert = []

    for item in staged_log:
        assert item.action == 'update'
        operations.move_to_commited(item.log_action)
        to_revert.append(item.uid)

    change.revert_uids(sorted(to_revert, reverse=True))
    ModelMeta.save_all_lazy()

    staged_log = change.stage_changes()

    assert len(staged_log) == 2
    for item in staged_log:
        assert item.diff == [['change', 'a', ['', '9']]]


def test_revert_removal():
    res = DBResource.from_dict('test1',
                               {'name': 'test1',
                                'base_path': 'x',
                                'state': RESOURCE_STATE.created.name,
                                'meta_inputs': {'a': {'value': None,
                                                      'schema': 'str'}}})
    res.inputs['a'] = '9'
    res.save_lazy()

    commited = CommitedResource.from_dict('test1', {'inputs': {'a': '9'},
                                                    'state': 'operational'})
    commited.save_lazy()

    resource_obj = resource.load(res.name)
    resource_obj.remove()
    ModelMeta.save_all_lazy()

    changes = change.stage_changes()
    assert len(changes) == 1
    assert changes[0].diff == [['remove', '', [['a', '9']]]]
    operations.move_to_commited(changes[0].log_action)

    ModelMeta.session_start()
    assert DBResource._c.obj_cache == {}
    assert DBResource.bucket.get('test1').siblings == []

    with mock.patch.object(resource, 'read_meta') as mread:
        mread.return_value = {
            'input': {'a': {'schema': 'str!'}},
            'id': 'mocked'
        }
        change.revert(changes[0].uid)
    ModelMeta.save_all_lazy()
    assert len(DBResource.bucket.get('test1').siblings) == 1

    resource_obj = resource.load('test1')
    assert resource_obj.args == {
        'a': '9',
        'location_id': '',
        'transports_id': ''
    }


@mark.xfail(
    reason="""With current approach child will
 notice changes after parent is removed"""
)
def test_revert_removed_child():
    res1 = orm.DBResource(id='test1', name='test1', base_path='x')  # NOQA
    res1.save()
    res1.add_input('a', 'str', '9')

    res2 = orm.DBResource(id='test2', name='test2', base_path='x')  # NOQA
    res2.save()
    res2.add_input('a', 'str', 0)

    res1 = resource.load('test1')
    res2 = resource.load('test2')
    signals.connect(res1, res2)

    staged_log = change.stage_changes()
    assert len(staged_log) == 2
    for item in staged_log:
        operations.move_to_commited(item.log_action)
    res2.remove()

    staged_log = change.stage_changes()
    assert len(staged_log) == 1
    logitem = next(staged_log.collection())
    operations.move_to_commited(logitem.log_action)

    with mock.patch.object(resource, 'read_meta') as mread:
        mread.return_value = {'input': {'a': {'schema': 'str!'}}}
        change.revert(logitem.uid)

    res2 = resource.load('test2')
    assert res2.args == {'a': '9'}


def test_revert_create():
    res = DBResource.from_dict('test1',
                               {'name': 'test1',
                                'base_path': 'x',
                                'state': RESOURCE_STATE.created.name,
                                'meta_inputs': {'a': {'value': None,
                                                      'schema': 'str'}}})
    res.inputs['a'] = '9'
    res.save_lazy()
    ModelMeta.save_all_lazy()

    staged_log = change.stage_changes()
    assert len(staged_log) == 1
    logitem = staged_log[0]
    operations.move_to_commited(logitem.log_action)
    assert logitem.diff == [['add', '', [['a', '9']]]]

    commited = CommitedResource.get('test1')
    assert commited.inputs == {'a': '9'}

    change.revert(logitem.uid)

    staged_log = change.stage_changes()
    assert len(staged_log) == 1
    for item in staged_log:
        operations.move_to_commited(item.log_action)
    assert resource.load_all() == []


def test_discard_all_pending_changes_resources_created():
    res1 = DBResource.from_dict('test1',
                                {'name': 'test1',
                                 'base_path': 'x',
                                 'state': RESOURCE_STATE.created.name,
                                 'meta_inputs': {'a': {'value': None,
                                                       'schema': 'str'}}})
    res1.inputs['a'] = '9'
    res1.save_lazy()

    res2 = DBResource.from_dict('test2',
                                {'name': 'test2',
                                 'base_path': 'x',
                                 'state': RESOURCE_STATE.created.name,
                                 'meta_inputs': {'a': {'value': None,
                                                       'schema': 'str'}}})
    res2.inputs['a'] = '0'
    res2.save_lazy()
    ModelMeta.save_all_lazy()

    staged_log = change.stage_changes()
    assert len(staged_log) == 2

    change.discard_all()
    staged_log = change.stage_changes()
    assert len(staged_log) == 0
    assert resource.load_all() == []


def test_discard_connection():
    res1 = DBResource.from_dict('test1',
                                {'name': 'test1',
                                 'base_path': 'x',
                                 'state': RESOURCE_STATE.created.name,
                                 'meta_inputs': {'a': {'value': None,
                                                       'schema': 'str'}}})
    res1.inputs['a'] = '9'
    res1.save_lazy()

    res2 = DBResource.from_dict('test2',
                                {'name': 'test2',
                                 'base_path': 'x',
                                 'state': RESOURCE_STATE.created.name,
                                 'meta_inputs': {'a': {'value': None,
                                                       'schema': 'str'}}})
    res2.inputs['a'] = '0'
    res2.save_lazy()
    ModelMeta.save_all_lazy()

    staged_log = change.stage_changes()
    for item in staged_log:
        operations.move_to_commited(item.log_action)

    res1 = resource.load('test1')
    res2 = resource.load('test2')
    res1.connect(res2, {'a': 'a'})
    staged_log = change.stage_changes()
    assert len(staged_log) == 1
    assert res2.args == {'a': '9'}
    change.discard_all()
    assert res2.args == {'a': '0'}
    assert len(change.stage_changes()) == 0


def test_discard_removed():
    res1 = DBResource.from_dict('test1',
                                {'name': 'test1',
                                 'base_path': 'x',
                                 'state': RESOURCE_STATE.created.name,
                                 'meta_inputs': {'a': {'value': None,
                                                       'schema': 'str'}}})
    res1.inputs['a'] = '9'
    res1.save_lazy()
    ModelMeta.save_all_lazy()
    staged_log = change.stage_changes()
    for item in staged_log:
        operations.move_to_commited(item.log_action)
    res1 = resource.load('test1')
    res1.remove()
    assert len(change.stage_changes()) == 1
    assert res1.to_be_removed()

    change.discard_all()

    assert len(change.stage_changes()) == 0
    assert not resource.load('test1').to_be_removed()


def test_discard_update():
    res1 = DBResource.from_dict('test1',
                                {'name': 'test1',
                                 'base_path': 'x',
                                 'state': RESOURCE_STATE.created.name,
                                 'meta_inputs': {'a': {'value': None,
                                                       'schema': 'str'}}})
    res1.inputs['a'] = '9'
    res1.save_lazy()
    ModelMeta.save_all_lazy()
    staged_log = change.stage_changes()
    for item in staged_log:
        operations.move_to_commited(item.log_action)
    res1 = resource.load('test1')
    res1.update({'a': '11'})
    assert len(change.stage_changes()) == 1
    assert res1.args == {'a': '11'}

    change.discard_all()
    assert res1.args == {'a': '9'}
