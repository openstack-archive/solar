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
from solar.core.resource import stage_resources
from solar.dblayer.model import ModelMeta
from solar.dblayer.solar_models import CommitedResource
from solar.dblayer.solar_models import Resource as DBResource
from solar.system_log import change
from solar.system_log import operations


def create_resource(name, tags=None, inputs=None):
    if inputs is None:
        inputs = {'a': ''}
    meta_inputs = {}
    for key, value in inputs.items():
        if not isinstance(value, basestring):
            raise Exception('Only strings are allowed')
        meta_inputs[key] = {'value': value, 'schema': 'str'}
    res = DBResource.from_dict(
        name,
        {'name': name,
         'base_path': 'x',
         'state': resource.RESOURCE_STATE.created.name,
         'tags': tags or [],
         'meta_inputs': meta_inputs,
         'inputs': meta_inputs})
    res.save_lazy()
    return resource.Resource(res)


def test_revert_update():
    prev = {'a': '9'}
    new = {'a': '10'}
    res = create_resource('test1')
    ModelMeta.save_all_lazy()

    res.update(prev)
    ModelMeta.save_all_lazy()
    logitem = change.staged_log()[0]
    operations.commit_log_item(logitem)
    res.update(new)
    ModelMeta.save_all_lazy()
    logitem = change.staged_log()[0]
    uid = logitem.uid
    assert logitem.diff == [['change', 'a', ['9', '10']]]
    operations.commit_log_item(logitem)
    assert res.args == new

    change.revert(uid)
    assert res.args == {'a': '9'}


def test_revert_update_connected():
    res1 = create_resource('test1')
    res1.update({'a': '9'})

    res2 = create_resource('test2')
    res2.update({'a': ''})

    res3 = create_resource('test3')
    res3.update({'a': ''})

    res1 = resource.load('test1')
    res2 = resource.load('test2')
    res3 = resource.load('test3')
    res1.connect(res2)
    res2.connect(res3)
    ModelMeta.save_all_lazy()

    staged_items = change.staged_log()
    assert len(staged_items) == 3

    for item in staged_items:
        assert item.action == 'run'
        operations.commit_log_item(item)

    res1.disconnect(res2)
    staged_log = change.staged_log()
    to_revert = []

    for item in staged_log:
        assert item.action == 'run'
        to_revert.append(item.uid)
        operations.commit_log_item(item)

    change.revert_uids(sorted(to_revert, reverse=True))
    ModelMeta.save_all_lazy()

    staged_log = change.staged_log()

    for item in staged_log:
        assert item.diff == [['change', 'a', ['', '9']]]


def test_only_relevant_child_updated():
    res1, res2, res3 = (
        create_resource(
            name, inputs={'a': '', 'b': ''}) for name in ('t1', 't2', 't3'))
    res1.update({'a': '9', 'b': '10'})
    res1.connect(res2, {'a': 'a'})
    res1.connect(res3, {'b': 'b'})
    ModelMeta.save_all_lazy()
    # currently childs added as a side effect of staged log, thus we need
    # to run it before commiting changes
    assert set(s.resource for s in change.staged_log()) == {'t1', 't2', 't3'}
    change.commit_all()
    res1.update({'a': '12'})
    ModelMeta.save_all_lazy()
    # t3 not updated because "a" connected only to t2
    assert set(s.resource for s in change.staged_log()) == {'t1', 't2'}


def test_discard_removed_with_childs_not_affected():
    res1, res2, res3 = (
        create_resource(
            name, inputs={'a': '', 'b': ''}) for name in ('t1', 't2', 't3'))
    res1.update({'a': '9', 'b': '10'})
    res1.connect(res2, {'a': 'a'})
    res1.connect(res3, {'b': 'b'})
    ModelMeta.save_all_lazy()
    change.staged_log()
    change.commit_all()
    res1.remove()
    ModelMeta.save_all_lazy()
    staged_items = change.staged_log()
    assert len(staged_items) == 1
    assert staged_items[0].log_action == 't1.remove'
    change.discard_all()
    assert not res1.to_be_removed()
    assert not res2.to_be_removed()
    assert not res3.to_be_removed()
    assert change.staged_log() == []


def test_revert_removal():
    res = create_resource('test1')
    commited = CommitedResource.from_dict('test1', {'inputs': {'a': '9'},
                                                    'state': 'operational'})
    commited.save_lazy()

    resource_obj = resource.load(res.name)
    resource_obj.remove()
    ModelMeta.save_all_lazy()

    staged_items = change.staged_log()
    assert len(staged_items) == 1
    log_item = staged_items[0]
    uid = log_item.uid
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
            change.revert(uid)

    ModelMeta.save_all_lazy()

    resource_obj = resource.load('test1')
    assert resource_obj.args == {
        'a': '9',
        'location_id': '',
        'transports_id': ''
    }


def test_revert_create():
    res = create_resource('test1')
    res.db_obj.inputs['a'] = '9'
    logitem = change.create_run(res)
    assert logitem.diff == [['add', '', [['a', '9']]]]
    uid = logitem.uid
    operations.commit_log_item(logitem)

    commited = CommitedResource.get('test1')
    assert commited.inputs == {'a': '9'}

    change.revert(uid)
    ModelMeta.save_all_lazy()
    staged_log = change.staged_log()
    assert len(staged_log) == 1
    for item in staged_log:
        operations.commit_log_item(item)

    assert resource.load_all() == []


def test_discard_all_pending_changes_resources_created():
    res1 = create_resource('test1')
    res1.db_obj.inputs['a'] = '9'
    res1.db_obj.save_lazy()

    res2 = create_resource('test2')
    res2.db_obj.inputs['a'] = '0'
    res2.db_obj.save_lazy()
    staged_log = map(change.create_run, (res1, res2))

    change.discard_all()
    staged_log = change.staged_log()
    assert len(staged_log) == 0
    assert resource.load_all() == []


def test_discard_connection():
    res1 = create_resource('test1')
    res1.db_obj.inputs['a'] = '9'
    res1.db_obj.save_lazy()

    res2 = create_resource('test2')
    res2.db_obj.inputs['a'] = '0'
    res2.db_obj.save_lazy()

    staged_log = map(change.create_run, (res1, res2))
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
    res1 = create_resource('test1')
    res1.db_obj.inputs['a'] = '9'
    res1.db_obj.save_lazy()

    res1 = resource.load('test1')
    res1.remove()
    ModelMeta.save_all_lazy()
    assert len(change.staged_log()) == 1
    assert res1.to_be_removed()

    change.discard_all()

    assert len(change.staged_log()) == 0
    assert not resource.load('test1').to_be_removed()


def test_discard_update():
    res1 = create_resource('test1')
    res1.db_obj.inputs['a'] = '9'
    operations.commit_log_item(change.create_run(res1))
    res1.update({'a': '11'})
    ModelMeta.save_all_lazy()
    assert len(change.staged_log()) == 1
    assert res1.args == {'a': '11'}

    change.discard_single(change.staged_log()[0])
    assert res1.args == {'a': '9'}


def test_stage_and_process_partially():
    a = ['a']
    b = ['b']
    both = a + b
    range_a = range(1, 4)
    range_b = range(4, 6)
    with_tag_a = [create_resource(str(n), tags=a) for n in range_a]
    with_tag_b = [create_resource(str(n), tags=b) for n in range_b]
    ModelMeta.save_all_lazy()
    created_log_items_with_a = stage_resources(a, 'restart')
    assert len(created_log_items_with_a) == len(with_tag_a)
    created_log_items_with_b = stage_resources(b, 'restart')
    assert len(created_log_items_with_b) == len(with_tag_b)

    a_graph = change.send_to_orchestration(a)
    a_expected = set(['%s.restart' % n for n in range_a])
    assert set(a_graph.nodes()) == a_expected
    b_graph = change.send_to_orchestration(b)
    b_expected = set(['%s.restart' % n for n in range_b])
    assert set(b_graph.nodes()) == b_expected
    both_graph = change.send_to_orchestration(both)
    assert set(both_graph.nodes()) == a_expected | b_expected


def test_childs_added_on_stage():
    res_0, res_1 = [create_resource(str(n)) for n in range(2)]
    ModelMeta.save_all_lazy()
    for res in (res_0, res_1):
        change.create_run(res)
    res_0.connect(res_1, {'a': 'a'})
    change.staged_log()
    ModelMeta.save_all_lazy()
    change.commit_all()
    res_0.update({'a': '10'})
    ModelMeta.save_all_lazy()
    staged_log = change.staged_log()
    assert len(staged_log) == 2
    child_log_item = next(li for li in staged_log
                          if li.resource == res_1.name)
    assert child_log_item.action == 'update'


def test_update_action_after_commit():
    res = resource.load(create_resource('1').name)
    res.set_operational()
    res.update({'a': 10})
    ModelMeta.save_all_lazy()
    staged_log = change.staged_log()
    assert staged_log[0].action == 'update'
