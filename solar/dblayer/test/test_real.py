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

from __future__ import print_function

import pytest

from solar.config import C
from solar.dblayer.conflict_resolution import SiblingsError
from solar.dblayer.model import check_state_for
from solar.dblayer.model import clear_cache
from solar.dblayer.model import StrInt
from solar.dblayer.solar_models import DBLayerSolarException
from solar.dblayer.solar_models import InputAlreadyExists
from solar.dblayer.solar_models import Lock
from solar.dblayer.solar_models import Resource
from solar.dblayer.solar_models import UnknownInput


def create_resource(key, data):
    mi = data.get('meta_inputs', {})
    for inp_name, inp_value in data.get('inputs', {}).items():
        if isinstance(inp_value, list):
            if len(inp_value) == 1 and isinstance(inp_value[0], dict):
                schema = [{}]
            else:
                schema = ['str!']
        elif isinstance(inp_value, dict):
            schema = {}
        else:
            if inp_value is None:
                mi.setdefault(inp_name, {})
                continue
            schema = '%s!' % type(inp_value).__name__
        mi.setdefault(inp_name, {"schema": schema})
    data['meta_inputs'] = mi
    return Resource.from_dict(key, data)


@pytest.mark.xfail(reason="Not YET decided how it should work")
def test_changes_state(rk):
    key = next(rk)
    r = create_resource(key, {'name': 'a name'})
    r.inputs['a'] = 1
    with pytest.raises(Exception):
        # raise exception when something is changed
        r.inputs['a']
    r.save()
    check_state_for('index', r)


def test_basic_input(rk):
    key = next(rk)
    r = create_resource(key, {'name': 'a name',
                              'inputs': {'a': None}})
    r.inputs['a'] = 1
    r.save()
    assert r.inputs['a'] == 1
    assert len(r._riak_object.indexes) == 2
    del r.inputs['a']
    r.save()
    with pytest.raises(DBLayerSolarException):
        assert r.inputs['a'] == 1
    assert len(r._riak_object.indexes) == 1


def test_input_in_dict(rk):
    key = next(rk)
    r = create_resource(key, {'name': 'a name',
                              'inputs': {'input1': 15,
                                         'input2': None}})
    r.save()
    assert r._riak_object.data['inputs']['input1'] == 15
    assert r.inputs['input1'] == 15

    assert r._riak_object.data['inputs']['input2'] is None
    assert r.inputs['input2'] is None


def test_basic_connect(rk):
    k1 = next(rk)
    k2 = next(rk)

    r1 = create_resource(k1, {'name': 'first',
                              'inputs': {'input1': 10,
                                         'input2': 15}})
    r2 = create_resource(k2, {'name': 'second',
                              'inputs': {'input1': None,
                                         'input2': None}})

    r1.connect(r2, {'input1': 'input1', 'input2': 'input2'})
    r1.save()
    r2.save()

    assert r1._riak_object.data['inputs']['input1'] == 10
    assert r1.inputs['input1'] == 10

    assert r2._riak_object.data['inputs']['input1'] is None
    assert r2.inputs['input1'] == 10

    assert r1._riak_object.data['inputs']['input2'] == 15
    assert r1.inputs['input2'] == 15

    assert r2._riak_object.data['inputs']['input2'] is None
    assert r2.inputs['input2'] == 15


@pytest.mark.parametrize('depth', (3, 4, 5, 10, 25, 50))
def test_adv_connect(rk, depth):
    k1 = next(rk)
    k2 = next(rk)

    r1 = create_resource(k1, {'name': 'first',
                              'inputs': {'input1': 10,
                                         'input2': 15}})
    prev = create_resource(k2, {'name': 'second',
                                'inputs': {'input1': None,
                                           'input2': None,
                                           'input3': 0}})
    conn = {'input1': 'input1', 'input2': 'input2'}
    r1.save()
    r1.connect(prev, conn)
    prev.save()
    created = [prev]

    for x in xrange(depth - 1):
        k = next(rk)
        res = create_resource(k, {'name': 'next %d' % (x + 1),
                                  'inputs': {'input1': None,
                                             'input2': None,
                                             'input3': x + 1}})
        created.append(res)
        prev.connect(res, conn)
        res.save()
        prev = res

    for i, c in enumerate(created):
        assert c.inputs['input1'] == 10
        assert c.inputs['input2'] == 15
        assert c.inputs['input3'] == i


@pytest.mark.parametrize('depth', (1, 3, 5, 10, 50, 100))
def test_perf_inputs(rk, depth):
    k1 = next(rk)
    r1 = create_resource(k1, {'name': 'first', 'inputs': {'input1': 'target'}})

    r1.save()
    prev = r1
    for x in xrange(depth):
        k = next(rk)
        res = create_resource(k, {'name': 'next %d' % (x + 1),
                                  'inputs': {'input1': None}})
        prev.connect(res, {'input1': 'input1'})
        res.save()
        prev = res

    import time
    st = time.time()
    assert res.inputs['input1'] == 'target'
    end = time.time()
    print(end - st)


def test_change_connect(rk):
    k1 = next(rk)
    k2 = next(rk)
    k3 = next(rk)

    r1 = create_resource(k1, {'name': 'first',
                              'inputs': {'input1': 10,
                                         'input2': 15}})
    r2 = create_resource(k2, {'name': 'second',
                              'inputs': {'input1': None,
                                         'input2': None,
                                         'input3': 0}})
    r3 = create_resource(k3, {'name': 'first',
                              'inputs': {'input1': 30,
                                         'input2': 35}})

    r1.connect(r2, {'input1': 'input1', 'input2': 'input2'})
    r3.connect(r2, {'input1': 'input1'})

    r1.save()
    r2.save()
    r3.save()

    assert r2.inputs['input1'] == 30
    assert r2.inputs['input2'] == 15


def test_simple_tag(rk, rt):
    k1 = next(rk)
    tag = next(rt)

    r1 = create_resource(k1, {'name': 'first',
                              'tags': ['%s' % tag, '%s=10' % tag]})

    r1.save()
    assert list(r1.tags) == ['%s=' % tag, '%s=10' % tag]


def test_list_by_tag(rk, rt):
    k1 = next(rk)
    k2 = next(rk)
    tag1 = next(rt)
    tag2 = next(rt)
    r1 = create_resource(k1, {'name': 'first', 'tags': [tag1, '%s=10' % tag1]})
    r1.save()

    r2 = create_resource(k2, {'name': 'first', 'tags': [tag1, '%s=10' % tag2]})
    r2.save()

    assert len(Resource.tags.filter(tag1)) == 2
    assert Resource.tags.filter(tag1) == set([k1, k2])
    assert len(Resource.tags.filter('other_tag')) == 0

    assert len(Resource.tags.filter(tag2)) == 0
    assert len(Resource.tags.filter(tag2, 10)) == 1
    assert Resource.tags.filter(tag2, 10) == set([k2])

    assert len(Resource.tags.filter(tag2, '*')) == 1


def test_updated_behaviour(rk):
    k1 = next(rk)

    _cmp = StrInt()
    r1 = create_resource(k1, {'name': 'blah'})
    r1.save()
    assert isinstance(r1._riak_object.data['updated'], basestring)
    assert not isinstance(r1.updated, basestring)
    assert r1.updated >= _cmp
    assert k1 in Resource.updated.filter(StrInt.p_min(), StrInt.p_max())


def test_updated_only_last(rk):

    for i in range(3):
        r = create_resource(next(rk), {'name': str(i)})
        r.save()
    assert Resource.updated.filter(r.updated, StrInt.p_max()) == [r.key]


def test_list_inputs(rk):
    k1 = next(rk)
    k2 = next(rk)

    r1 = create_resource(k1, {'name': 'first',
                              'inputs': {'input1': 10,
                                         'input2': 15}})
    r2 = create_resource(k2, {'name': 'second', 'inputs': {'input': []}})

    r1.connect(r2, {'input1': 'input'})
    r1.connect(r2, {'input2': 'input'})

    r1.save()
    r2.save()

    assert r2.inputs['input'] == [10, 15]


def test_dict_to_dict_inputs(rk):
    k1 = next(rk)
    k2 = next(rk)

    r1 = create_resource(k1, {'name': 'first',
                              'inputs': {'input': {'input1': 10,
                                                   'input2': 15}}})
    r2 = create_resource(k2, {'name': 'second',
                              'inputs': {'input': {'input1': None,
                                                   'input2': None,
                                                   'input3': None}}})

    r1.connect(r2, {'input': 'input'})
    r1.save()
    r2.save()

    assert r2.inputs['input']['input1'] == 10
    assert r2.inputs['input']['input2'] == 15
    assert 'input3' not in r2.inputs['input']


def test_list_to_list_inputs(rk):
    k1 = next(rk)
    k2 = next(rk)

    r1 = create_resource(k1, {'name': 'first', 'inputs': {'input': [10, 15]}})
    r2 = create_resource(k2, {'name': 'second', 'inputs': {'input': []}})

    r1.connect(r2, {'input': 'input'})

    r1.save()
    r2.save()

    assert r2.inputs['input'] == [10, 15]


def test_simple_to_dict_inputs(rk):
    k1 = next(rk)
    k2 = next(rk)

    r1 = create_resource(k1, {'name': 'first',
                              'inputs': {'input1': 10,
                                         'input2': 15}})
    r2 = create_resource(k2, {'name': 'second',
                              'inputs': {'input': {'input1': None,
                                                   'input2': None}}})

    r1.connect(r2, {'input1': 'input:input1', 'input2': 'input:input2'})

    r1.save()
    r2.save()

    assert r2.inputs['input']['input1'] == 10
    assert r2.inputs['input']['input2'] == 15


def test_simple_to_dict_inputs_without_tag_single_key(rk):
    k1 = next(rk)
    k2 = next(rk)

    r1 = create_resource(k1, {'name': 'first',
                              'inputs': {'input1': 10,
                                         'input2': 15}})
    r2 = create_resource(k2, {'name': 'second',
                              'inputs': {'input': {'input1': None,
                                                   'input2': None}}})

    r1.connect(r2, {'input1': 'input:input1'})

    r1.save()
    r2.save()

    assert r2.inputs['input']['input1'] == 10


def test_simple_to_dict_inputs_without_tag(rk):
    k1 = next(rk)
    k2 = next(rk)
    k3 = next(rk)

    r1 = create_resource(k1, {'name': 'first',
                              'inputs': {'input1': 10,
                                         'input2': 15}})
    r3 = create_resource(k3, {'name': 'third',
                              'inputs': {'input1': 110,
                                         'input2': 115}})
    r2 = create_resource(k2, {'name': 'second',
                              'inputs': {'input': {'input1': None,
                                                   'input2': None}}})

    r1.connect(r2, {'input1': 'input:input1'})
    r3.connect(r2, {'input2': 'input:input2'})

    r1.save()
    r2.save()
    r3.save()

    assert r2.inputs['input']['input1'] == 10
    assert r2.inputs['input']['input2'] == 115


def test_simple_to_dict_inputs_with_tag(rk):
    k1 = next(rk)
    k2 = next(rk)
    k3 = next(rk)

    r1 = create_resource(k1, {'name': 'first',
                              'inputs': {'input1': 10,
                                         'input2': 15}})
    r3 = create_resource(k3, {'name': 'first',
                              'inputs': {'input1': 110,
                                         'input2': 115}})
    r2 = create_resource(k2, {'name': 'second',
                              'inputs': {'input': {'input1': None,
                                                   'input2': None}}})

    r1.connect(r2, {'input1': 'input:input1|tag'})
    r3.connect(r2, {'input2': 'input:input2|tag'})

    r1.save()
    r2.save()
    r3.save()

    assert r2.inputs['input']['input1'] == 10
    assert r2.inputs['input']['input2'] == 115


def test_simple_to_listdict_inputs(rk):

    k1 = next(rk)
    k2 = next(rk)
    k3 = next(rk)
    k4 = next(rk)

    r1 = create_resource(k1, {'name': 'first',
                              'inputs': {'input1': 10,
                                         'input2': 15}})
    r3 = create_resource(k3, {'name': 'first',
                              'inputs': {'input1': 110,
                                         'input2': 115}})
    r4 = create_resource(k4, {'name': 'first',
                              'inputs': {'input1': 1110,
                                         'input2': 1115}})
    r2 = create_resource(k2, {'name': 'second',
                              'inputs': {'input': [{'input1': None,
                                                    'input2': None}]}})

    r1.connect(r2, {'input1': 'input:input1', 'input2': 'input:input2'})
    r3.connect(r2, {'input2': 'input:input2|tag2',
                    'input1': 'input:input1|tag1'})
    r4.connect(r2, {'input2': 'input:input2|tag1',
                    'input1': 'input:input1|tag2'})

    r1.save()
    r2.save()
    r3.save()
    r4.save()

    inputs = set(pytest.dicts_to_hashable(r2.inputs['input']))
    expected_inputs = set(pytest.dicts_to_hashable(
        [{u'input2': 1115, u'input1': 110},
         {u'input2': 115, u'input1': 1110},
         {u'input2': 15, u'input1': 10}]))

    assert inputs == expected_inputs


def test_dict_to_list_inputs(rk):

    k1 = next(rk)
    k2 = next(rk)
    k3 = next(rk)

    r1 = create_resource(k1, {'name': 'first', 'inputs': {'modules': [{}]}})
    r2 = create_resource(k2, {'name': 'second',
                              'inputs': {'module': {'name': 'blah2'}}})
    r3 = create_resource(k3, {'name': 'third',
                              'inputs': {'module': {'name': 'blah3'}}})

    r2.connect(r1, {'module': 'modules'})
    r3.connect(r1, {'module': 'modules'})
    r1.save()
    r2.save()
    r3.save()

    assert sorted(r1.inputs['modules']) == sorted([{'name': 'blah2'},
                                                   {'name': 'blah3'}])


def test_passthrough_inputs(rk):

    k1 = next(rk)
    k2 = next(rk)
    k3 = next(rk)

    r1 = create_resource(k1, {'name': 'first',
                              'inputs': {'input1': 10,
                                         'input2': 15}})
    r2 = create_resource(k2, {'name': 'first',
                              'inputs': {'input1': None,
                                         'input2': None}})
    r3 = create_resource(k3, {'name': 'first',
                              'inputs': {'input1': None,
                                         'input2': None}})

    r2.connect(r3, {'input1': 'input1', 'input2': 'input2'})
    r1.connect(r2, {'input1': 'input1', 'input2': 'input2'})

    r1.save()
    r2.save()
    r3.save()

    assert r3.inputs['input1'] == 10
    assert r3.inputs['input2'] == 15


def test_disconnect_by_input(rk):
    k1 = next(rk)
    k2 = next(rk)
    k3 = next(rk)

    r1 = create_resource(k1, {'name': 'first',
                              'inputs': {'input1': 10,
                                         'input2': 15}})
    r2 = create_resource(k2, {'name': 'first',
                              'inputs': {'input1': None,
                                         'input2': None}})
    r3 = create_resource(k3, {'name': 'first',
                              'inputs': {'input1': None,
                                         'input2': None}})

    r2.connect(r3, {'input1': 'input1', 'input2': 'input2'})
    r1.connect(r2, {'input1': 'input1', 'input2': 'input2'})

    r1.save()
    r2.save()
    r3.save()

    with pytest.raises(Exception):
        r2.inputs['input1'] = 150

    r2.inputs.disconnect('input1')

    r2.save()

    assert r2.inputs['input1'] is None

    r2.inputs['input1'] = 150

    r2.save()

    assert r2.inputs['input1'] == 150
    assert r2.inputs['input2'] == 15

    assert r3.inputs['input1'] == 150


def test_resource_childs(rk):
    k1 = next(rk)
    k2 = next(rk)
    k3 = next(rk)

    r1 = create_resource(k1, {'name': 'first',
                              'inputs': {'input1': 10,
                                         'input2': 15}})
    r2 = create_resource(k2, {'name': 'first',
                              'inputs': {'input1': None,
                                         'input2': None}})
    r3 = create_resource(k3, {'name': 'first',
                              'inputs': {'input1': None,
                                         'input2': None}})

    r2.connect(r3, {'input1': 'input1'})
    r1.connect(r2, {'input1': 'input1'})

    r1.save()
    r2.save()
    r3.save()

    assert set(Resource.childs([r1.key])) == {r1.key, r2.key, r3.key}


def test_events(rk):
    k = next(rk)
    r1 = Resource.from_dict(k, {'events': ['event1', 'event2']})
    r1.save()
    assert r1.events == ['event1', 'event2']
    r1.events.pop()

    assert r1.events == ['event1']


def test_delete(rk):
    k1 = next(rk)
    k2 = next(rk)

    r1 = create_resource(k1, {'name': 'first',
                              'inputs': {'input1': 10,
                                         'input2': 15}})
    r2 = create_resource(k2, {'name': 'first',
                              'inputs': {'input1': None,
                                         'input2': None}})

    r1.connect(r2, {'input1': 'input1'})
    r1.save()
    r2.save()

    r1.delete()

    recv_emit_bin = []
    for index in r2._riak_object.indexes:
        if 'recv' in index[0] or 'emit' in index[0]:
            recv_emit_bin.append(index)
    assert recv_emit_bin == []


def test_delete_hash(rk):
    k1 = next(rk)
    k2 = next(rk)

    r1 = create_resource(k1, {'name': 'first',
                              'inputs': {'input1': 10,
                                         'input2': 15}})
    r2 = create_resource(k2, {'name': 'second',
                              'inputs': {'input': {'input1': None,
                                                   'input2': None}}})

    r1.connect(r2, {'input1': 'input:input1', 'input2': 'input:input2'})

    r1.save()
    r2.save()

    r1.delete()
    recv_emit_bin = []
    for index in r2._riak_object.indexes:
        if 'recv' in index[0] or 'emit' in index[0]:
            recv_emit_bin.append(index)
    assert recv_emit_bin == []


def test_nested_simple_listdict(rk):
    k1 = next(rk)
    k2 = next(rk)
    k3 = next(rk)
    k4 = next(rk)
    k5 = next(rk)

    r1 = create_resource(k1, {'name': 'first',
                              'inputs': {'config': [{"backends": [{}],
                                                     'listen_port': 1}]}})
    r2 = create_resource(k2, {'name': 'second', 'inputs': {'backend': {}}})
    r3 = create_resource(k3, {'name': 'third', 'inputs': {'backend': {}}})
    r5 = create_resource(k5, {'name': 'fifth',
                              'inputs': {"port": 5,
                                         "host": "fifth_host"}})
    r4 = create_resource(k4, {'name': 'fourth',
                              'inputs': {"port": 4,
                                         "host": "fourth_host"}})

    r4.connect(r2, {'port': "backend:port", 'host': 'backend:host'})
    r5.connect(r3, {'port': "backend:port", 'host': 'backend:host'})

    assert r2.inputs['backend'] == {'host': 'fourth_host', 'port': 4}
    assert r3.inputs['backend'] == {'host': 'fifth_host', 'port': 5}

    r2.connect(r1, {'backend': 'config:backends'})
    r3.connect(r1, {'backend': 'config:backends'})

    Resource.save_all_lazy()

    backends = next(x['backends'] for x in r1.inputs['config']
                    if 'backends' in x)
    assert len(backends) == 2


def test_nested_two_listdict(rk):
    k1 = next(rk)
    k2 = next(rk)
    k3 = next(rk)

    r1 = create_resource(k1, {'name': 'first',
                              'inputs': {'config': [{"backends": [{}],
                                                     'something': 0}]}})
    r2 = create_resource(k2, {'name': 'second',
                              'inputs': {"backends": [{"host": "second_host",
                                                       "port": 2}],
                                         'something': 1}})
    r3 = create_resource(k3, {'name': 'third',
                              'inputs': {"backends": [{"host": "third_host",
                                                       "port": 3}],
                                         'something': 2}})

    r2.connect(r1, {'backends': 'config:backends',
                    'something': 'config:something'})
    r3.connect(r1, {'backends': 'config:backends',
                    'something': 'config:something'})

    Resource.save_all_lazy()

    for sc in r1.inputs['config']:
        assert 'something' in sc
        assert 'backends' in sc
        assert isinstance(sc['backends'], list)
        assert isinstance(sc['something'], int)


def test_connect_other_list(rk):
    k1 = next(rk)
    k2 = next(rk)

    r1 = create_resource(k1, {'name': 'first',
                              'inputs': {'config': {"trackers": []}}})
    r2 = create_resource(k2, {'name': 'second',
                              'inputs': {"trackers": ["t1", "t2"]}})
    r2.connect(r1, {'trackers': 'config:trackers'})
    Resource.save_all_lazy()

    assert r1.inputs['config']['trackers'] == ["t1", "t2"]


def test_raise_error_unknown_input(rk):
    k1 = next(rk)
    r1 = create_resource(k1, {'name': 'first',
                              'inputs': {'a': 10}})

    r1.save()

    with pytest.raises(UnknownInput):
        r1.inputs['b'] = 11


@pytest.mark.parametrize('schema', (None, 'int!'))
def test_add_new_input(rk, schema):
    k1 = next(rk)

    r1 = create_resource(k1, {'name': 'first',
                              'inputs': {'a': 10}})
    r1.save()
    r1.inputs.add_new('b', 15, schema)
    r1.save()
    assert r1.inputs['b'] == 15
    if schema:
        assert r1.meta_inputs['b']['schema'] == schema

    with pytest.raises(InputAlreadyExists):
        r1.inputs.add_new('b', 25, schema)


def test_remove_input(rk):
    k1 = next(rk)

    r1 = create_resource(k1, {'name': 'first',
                              'inputs': {'a': 10,
                                         'b': 15}})

    r1.save()
    r1.inputs.remove_existing('b')
    assert 'b' not in r1.inputs.keys()
    assert 'b' not in r1.meta_inputs.keys()

    with pytest.raises(DBLayerSolarException):
        r1.inputs.remove_existing('b')


@pytest.mark.skipif(
    not ('riak' in C.solar_db and not C.riak_ensemble),
    reason=('Siblings error on write is expected'
            ' only with n_val=1 and 1 node installation'))
def test_return_siblings_on_write(rk):
    riak = pytest.importorskip('riak')

    uid = next(rk)
    lock = Lock.from_dict(uid, {'identity': uid})
    lock.save()
    clear_cache()

    with pytest.raises(SiblingsError):
        lock1 = Lock.from_dict(uid, {'identity': uid})
        lock1.save()
    s1, s2 = lock1._riak_object.siblings
    assert s1.data == s2.data


@pytest.mark.skipif(
    not ('riak' in C.solar_db and C.riak_ensemble),
    reason='On update without turned on ensemble riak wont raise RiakError')
def test_raise_riak_error_on_incorrect_update(rk):
    riak = pytest.importorskip('riak')

    uid = next(rk)
    lock = Lock.from_dict(uid, {'identity': uid})
    lock.save()
    clear_cache()

    with pytest.raises(riak.RiakError):
        lock1 = Lock.from_dict(uid, {'identity': uid})
        lock1.save()


@pytest.mark.skipif(
    'sqlite' not in C.solar_db,
    reason='Force insert wont be used by other backends')
def test_non_unique_key(rk):
    peewee = pytest.importorskip('peewee')

    uid = next(rk)
    lock = Lock.from_dict(uid, {'identity': '1'})
    lock.save(force_insert=True)
    clear_cache()
    lock1 = Lock.from_dict(uid, {'identity': '2'})
    with pytest.raises(peewee.IntegrityError):
        lock1.save(force_insert=True)
