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

from solar.core.resource import repository
from solar.core.resource import resource
from solar.core.resource import RESOURCE_STATE
from solar.dblayer.model import ModelMeta
from solar.dblayer.solar_models import CommitedResource
from solar.dblayer.solar_models import Resource as DBResource
from solar.system_log import change
from solar.system_log import operations


def test_revert_update():
    prev = {'a': '9'}
    new = {'a': '10'}
    res = DBResource.from_dict('test1',
                               {'name': 'test1',
                                'base_path': 'x',
                                'state': '',
                                'meta_inputs': {'a': {'value': None,
                                                      'schema': 'str'}}})
    res.save()
    action = 'run'
    resource_obj = resource.load(res.name)

    resource_obj.update(prev)
    logitem = change.create_logitem(res.name, action)
    operations.commit_log_item(logitem)
    resource_obj.update(new)

    logitem = change.create_logitem(res.name, action)
    operations.commit_log_item(logitem)
    # needs to be saved, otherwise it wont be found in change.revert
    logitem.save()
    assert logitem.diff == [['change', 'a', ['9', '10']]]
    assert resource_obj.args == new

    change.revert(logitem.uid)
    assert resource_obj.args == {'a': '9'}


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

    staged_log = map(lambda res: change.create_run(res.name),
                     (res1, res2, res3))
    assert len(staged_log) == 3

    for item in staged_log:
        assert item.action == 'run'
        operations.commit_log_item(item)

    res1.disconnect(res2)
    staged_log = map(lambda res: change.create_run(res.name),
                     (res2, res3))
    to_revert = []

    for item in staged_log:
        assert item.action == 'run'
        operations.commit_log_item(item)
        to_revert.append(item.uid)
        item.save()

    change.revert_uids(sorted(to_revert, reverse=True))
    ModelMeta.save_all_lazy()

    staged_log = map(lambda res: change.create_run(res.name),
                     (res2, res3))

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

    log_item = change.create_remove(resource_obj.name)
    log_item.save()
    assert log_item.diff == [['remove', '', [['a', '9']]]]
    operations.commit_log_item(log_item)

    ModelMeta.save_all_lazy()

    with mock.patch.object(repository.Repository, 'read_meta') as mread:
        mread.return_value = {
            'input': {'a': {'schema': 'str!'}},
            'id': 'mocked'
        }
        with mock.patch.object(repository.Repository, 'get_path') as mpath:
            mpath.return_value = 'x'
            change.revert(log_item.uid)

    ModelMeta.save_all_lazy()

    resource_obj = resource.load('test1')
    assert resource_obj.args == {
        'a': '9',
        'location_id': '',
        'transports_id': ''
    }


def test_revert_create():
    res = DBResource.from_dict('test1',
                               {'name': 'test1',
                                'base_path': 'x',
                                'state': RESOURCE_STATE.created.name,
                                'meta_inputs': {'a': {'value': None,
                                                      'schema': 'str'}}})
    res.inputs['a'] = '9'
    res.save_lazy()

    logitem = change.create_run(res.name)
    operations.commit_log_item(logitem)
    assert logitem.diff == [['add', '', [['a', '9']]]]

    commited = CommitedResource.get('test1')
    assert commited.inputs == {'a': '9'}

    change.revert(logitem.uid)
    ModelMeta.save_all_lazy()
    staged_log = change.staged_log()
    assert len(staged_log) == 1
    for item in staged_log:
        operations.commit_log_item(item)

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
    staged_log = map(change.create_run, (res1.name, res2.name))

    change.discard_all()
    staged_log = change.staged_log()
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

    staged_log = map(change.create_run, (res1.name, res2.name))
    for item in staged_log:
        operations.commit_log_item(item)

    res1 = resource.load('test1')
    res2 = resource.load('test2')
    res1.connect(res2, {'a': 'a'})
    ModelMeta.save_all_lazy()
    staged_log = change.staged_log()
    assert len(staged_log) == 1
    assert res2.args == {'a': '9'}
    change.discard_all()
    assert res2.args == {'a': '0'}
    assert len(change.staged_log()) == 0


def test_discard_removed():
    res1 = DBResource.from_dict('test1',
                                {'name': 'test1',
                                 'base_path': 'x',
                                 'state': RESOURCE_STATE.created.name,
                                 'meta_inputs': {'a': {'value': None,
                                                       'schema': 'str'}}})
    res1.inputs['a'] = '9'
    res1.save_lazy()

    res1 = resource.load('test1')
    res1.remove()
    ModelMeta.save_all_lazy()
    assert len(change.staged_log()) == 1
    assert res1.to_be_removed()

    change.discard_all()

    assert len(change.staged_log()) == 0
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
    operations.commit_log_item(change.create_run(res1.name))
    res1 = resource.load('test1')
    res1.update({'a': '11'})
    assert len(change.staged_log()) == 1
    assert res1.args == {'a': '11'}

    change.discard_all()
    assert res1.args == {'a': '9'}
