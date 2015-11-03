import pytest
import random

from solar.dblayer.model import Model, Field, IndexField, clear_cache, check_state_for, StrInt
from solar.dblayer.solar_models import Resource, DBLayerSolarException


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
        val = r.inputs['a']
    r.save()
    check_state_for('index', r)


def test_basic_input(rk):
    key = next(rk)
    r = create_resource(key, {'name': 'a name'})
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

    assert r._riak_object.data['inputs']['input2'] == None
    assert r.inputs['input2'] == None


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

    assert r2._riak_object.data['inputs']['input1'] == None
    assert r2.inputs['input1'] == 10

    assert r1._riak_object.data['inputs']['input2'] == 15
    assert r1.inputs['input2'] == 15

    assert r2._riak_object.data['inputs']['input2'] == None
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
    r1 = create_resource(k1, {'name': 'first',
                                 'inputs': {'input1': 'target'}})

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
    print end - st


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
    r1 = create_resource(k1, {'name': 'first',
                                     'tags': [tag1, '%s=10' % tag1]})
    r1.save()

    r2 = create_resource(k2, {'name': 'first',
                                     'tags': [tag1, '%s=10' % tag2]})
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
    r2 = create_resource(k2, {'name': 'second',
                                 'inputs': {'input': []}})

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
                                                      'input2': 15}
                                            }})
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

    r1 = create_resource(k1, {'name': 'first',
                                 'inputs': {'input': [10, 15]}})
    r2 = create_resource(k2, {'name': 'second',
                                 'inputs': {'input': []}})

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


    r1.connect(r2, {'input1': 'input:input1',
                    'input2': 'input:input2'})

    r1.save()
    r2.save()

    assert r2.inputs['input']['input1'] == 10
    assert r2.inputs['input']['input2'] == 15


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


    r1.connect(r2, {'input1': 'input:input1',
                    'input2': 'input:input2'})
    r3.connect(r2, {'input2': 'input:input2|tag2',
                    'input1': 'input:input1|tag1'})
    r4.connect(r2, {'input2': 'input:input2|tag1',
                    'input1': 'input:input1|tag2'})

    r1.save()
    r2.save()
    r3.save()
    r4.save()

    assert r2.inputs['input'] == [{u'input2': 1115, u'input1': 110},
                                  {u'input2': 115, u'input1': 1110},
                                  {u'input2': 15, u'input1': 10}]


def test_dict_to_list_inputs(rk):

    k1 = next(rk)
    k2 = next(rk)
    k3 = next(rk)

    r1 = create_resource(k1, {'name': 'first',
                              'inputs': {'modules': [{}]}})
    r2 = create_resource(k2, {'name': 'second',
                              'inputs': {'module': {'name': 'blah2'}}})
    r3 = create_resource(k3, {'name': 'third',
                              'inputs': {'module': {'name': 'blah3'}}})

    r2.connect(r1, {'module': 'modules'})
    r3.connect(r1, {'module': 'modules'})
    r1.save()
    r2.save()
    r3.save()

    assert r1.inputs['modules'] == [{'name': 'blah2'}, {'name': 'blah3'}]




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

    r2.connect(r3, {'input1': 'input1',
                    'input2': 'input2'})
    r1.connect(r2, {'input1': 'input1',
                    'input2': 'input2'})

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

    r2.connect(r3, {'input1': 'input1',
                    'input2': 'input2'})
    r1.connect(r2, {'input1': 'input1',
                    'input2': 'input2'})

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
    r1.save()
    assert r1.events == ['event1']
