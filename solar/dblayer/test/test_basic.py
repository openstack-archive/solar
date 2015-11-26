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

import pytest

from solar.dblayer.model import clear_cache
from solar.dblayer.model import DBLayerException
from solar.dblayer.model import DBLayerNoRiakObj
from solar.dblayer.model import DBLayerNotFound
from solar.dblayer.model import Field
from solar.dblayer.model import IndexField
from solar.dblayer.model import Model
from solar.dblayer.model import StrInt


class M1(Model):

    f1 = Field(str)
    f2 = Field(int)
    f3 = Field(int, fname='some_field')

    ind = IndexField(default=dict)


class M2(Model):
    f1 = Field(str)

    ind = IndexField(default=dict)


class M3(Model):
    f1 = Field(str)

    ind = IndexField(default=dict)


def test_from_dict(rk):
    key = next(rk)

    with pytest.raises(DBLayerException):
        M1.from_dict({'f1': 'blah', 'f2': 150, 'some_field': 250})

    m1 = M1.from_dict({'key': key, 'f1': 'blah', 'f2': 150, 'some_field': 250})

    m1.save()
    m11 = M1.get(key)
    assert m1.key == key
    assert m1.f3 == 250
    assert m1 is m11


def test_not_exists(rk):
    key = next(rk)
    with pytest.raises(DBLayerNotFound):
        M1.get(key)

    m1 = M1.from_dict(key, {'f1': 'blah', 'f2': 150})
    m1.save()
    M1.get(key)


def test_update(rk):
    k = next(rk)
    m1 = M1.from_dict(k, {'f1': 'blah', 'f2': 150})
    m1.save()
    m1.f1 = 'blub'
    assert m1.f1 == 'blub'
    m1.save()
    assert m1.f1 == 'blub'
    m11 = M1.get(k)
    assert m11.f1 == 'blub'

    clear_cache()
    m12 = M1.get(k)
    assert m12.f1 == 'blub'


def test_lazy(rk):
    k = next(rk)
    m1 = M1.from_dict(k, {'f1': 'blah', 'f2': 150})
    m1.save()
    clear_cache()

    m1 = M1(k)
    with pytest.raises(DBLayerNoRiakObj):
        assert m1.f1 == 'blah'


def test_cache_logic(rk):
    k = next(rk)
    M1.session_start()
    assert M1._c.obj_cache == {}

    m1 = M1.from_dict(k, {'f1': 'blah', 'f2': 150})
    m1.save()
    M1.session_end()

    M1.session_start()
    assert M1._c.obj_cache == {}
    m11 = M1.get(k)
    pid = id(M1._c)
    assert M1._c.obj_cache == {k: m11}
    M1.session_end()

    M1.session_start()
    assert M1._c.obj_cache == {}
    M1.get(k)
    aid = id(M1._c)

    assert pid != aid


def test_normal_index(rk):
    key = next(rk)
    key2 = next(rk)

    m1 = M1.from_dict(key, {'f1': 'blah',
                            'f2': 150,
                            'ind': {'blah': 'something'}})
    m1.save()

    m2 = M1.from_dict(key2, {'f1': 'blah',
                             'f2': 150,
                             'ind': {'blah': 'something2'}})
    m2.save()
    assert set(M1.ind.filter('blah=somethi*')) == set([key, key2])
    assert set(M1.ind.filter('blah=something')) == set([key])
    assert set(M1.ind.filter('blah=something2')) == set([key2])


def test_update_behaviour(rk):
    key = next(rk)

    m1 = M1.from_dict(key, {'f1': 'blah', 'f2': 150})
    assert m1.changed() is True
    m1.save()

    assert m1.changed() is False
    with pytest.raises(DBLayerException):
        m1.save()

    m1.f1 = 'updated'
    assert m1.changed() is True

    m1.save()

    assert m1.f1 == 'updated'

    clear_cache()
    m11 = M1.get(key)
    assert m11.f1 == 'updated'


def test_different_models(rk):
    key = next(rk)

    m2 = M2.from_dict(key, {'f1': 'm2', 'ind': {'blah': 'blub'}})
    m3 = M3.from_dict(key, {'f1': 'm3', 'ind': {'blah': 'blub'}})

    m2.save()
    m3.save()

    assert M2.get(key).f1 == 'm2'
    assert M3.get(key).f1 == 'm3'


def test_cache_behaviour(rk):
    key1 = next(rk)

    m1 = M1.from_dict(key1, {'f1': 'm1'})

    m11 = M1.get(key1)
    assert m1 is m11
    m1.save()
    assert m1 is m11

    m12 = M1.get(key1)
    assert m1 is m12

    clear_cache()
    m13 = M1.get(key1)
    assert m1 is not m13


def test_save_lazy(rk):
    key1 = next(rk)
    key2 = next(rk)

    m1 = M1.from_dict(key1, {'f1': 'm1'})
    m2 = M1.from_dict(key2, {'f1': 'm2'})
    m1.save_lazy()
    m2.save_lazy()

    m1g = M1.get(key1)
    m2g = M1.get(key2)

    assert m1 is m1g
    assert m2 is m2g

    assert M1._c.lazy_save == {m1, m2}
    M1.session_end()
    assert M1._c.lazy_save == set()

    clear_cache()
    m1g2 = M1.get(key1)
    m2g2 = M1.get(key2)

    assert m1g is not m1g2
    assert m2g is not m2g2


def test_changed_index(rk):
    key1 = next(rk)

    m1 = M1.from_dict(key1, {'f1': 'm1'})

    m1.save()
    # don't use _add_index directly
    m1._add_index('test_bin', 'blah')
    m1.save()


def test_strint_comparsions():
    a = StrInt(-1)
    b = StrInt(-2)
    c = StrInt.to_simple(b)
    assert isinstance(c, basestring)
    assert a > b
    assert a > c


def test_delete_cache_behaviour(rk):
    key1 = next(rk)

    m1 = M1.from_dict(key1, {'f1': 'm1'})

    m1.save()

    clear_cache()

    M1.get(key1).delete()
    with pytest.raises(DBLayerNotFound):
        M1.get(key1)


def test_fast_delete(rk):
    key1 = next(rk)

    m1 = M1.from_dict(key1, {'f1': 'm1'})
    m1.save()
    m1.delete()
    M1.session_start()
    m12 = M1.from_dict(key1, {'f1': 'm12'})
    m12.save()
    assert m12.f1 == 'm12'
