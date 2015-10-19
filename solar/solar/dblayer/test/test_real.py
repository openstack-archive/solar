import pytest
import random

from solar.dblayer.model import Model, Field, IndexField, clear_cache, check_state_for
from solar.dblayer.solar_models import Resource, DBLayerSolarException



def test_changes_state(rk):
    key = next(rk)
    r = Resource.from_dict(key, {'name': 'a name'})
    r.inputs['a'] = 1
    with pytest.raises(Exception):
        # raise exception when something is changed
        val = r.inputs['a']
    r.save()
    check_state_for('index', r)


def test_basic_input(rk):
    key = next(rk)
    r = Resource.from_dict(key, {'name': 'a name'})
    r.inputs['a'] = 1
    r.save()
    assert r.inputs['a'] == 1
    assert len(r._riak_object.indexes) == 1
    del r.inputs['a']
    r.save()
    with pytest.raises(DBLayerSolarException):
        assert r.inputs['a'] == 1
    assert len(r._riak_object.indexes) == 0


def test_input_in_dict(rk):
    key = next(rk)
    r = Resource.from_dict(key, {'name': 'a name',
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

    r1 = Resource.from_dict(k1, {'name': 'first',
                                 'inputs': {'input1': 10,
                                            'input2': 15}})
    r2 = Resource.from_dict(k2, {'name': 'second',
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


@pytest.mark.parametrize('depth', (3, 4, 5, 10))
def test_adv_connect(rk, depth):
    k1 = next(rk)
    k2 = next(rk)

    r1 = Resource.from_dict(k1, {'name': 'first',
                                 'inputs': {'input1': 10,
                                            'input2': 15}})
    prev = Resource.from_dict(k2, {'name': 'second',
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
        res = Resource.from_dict(k, {'name': 'next %d' % (x + 1),
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
    r1 = Resource.from_dict(k1, {'name': 'first',
                                 'inputs': {'input1': 'target'}})

    r1.save()
    prev = r1
    for x in xrange(depth):
        k = next(rk)
        res = Resource.from_dict(k, {'name': 'next %d' % (x + 1),
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

    r1 = Resource.from_dict(k1, {'name': 'first',
                                 'inputs': {'input1': 10,
                                            'input2': 15}})
    r2 = Resource.from_dict(k2, {'name': 'second',
                                 'inputs': {'input1': None,
                                            'input2': None,
                                            'input3': 0}})
    r3 = Resource.from_dict(k3, {'name': 'first',
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

    r1 = Resource.from_dict(k1, {'name': 'first',
                                 'tags': ['%s' % tag, '%s=10' % tag]})

    r1.save()
    assert list(r1.tags) == ['%s=' % tag, '%s=10' % tag]


def test_list_by_tag(rk, rt):
    k1 = next(rk)
    k2 = next(rk)
    tag1 = next(rt)
    tag2 = next(rt)
    r1 = Resource.from_dict(k1, {'name': 'first',
                                     'tags': [tag1, '%s=10' % tag1]})
    r1.save()

    r2 = Resource.from_dict(k2, {'name': 'first',
                                     'tags': [tag1, '%s=10' % tag2]})
    r2.save()

    assert len(Resource.tags.filter(tag1)) == 2
    assert Resource.tags.filter(tag1) == set([k1, k2])
    assert len(Resource.tags.filter('other_tag')) == 0

    assert len(Resource.tags.filter(tag2)) == 0
    assert len(Resource.tags.filter(tag2, 10)) == 1
    assert Resource.tags.filter(tag2, 10) == set([k2])

    assert len(Resource.tags.filter(tag2, '*')) == 1
