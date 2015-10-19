import pytest
from solar.dblayer.model import (Field, IndexField,
                                 clear_cache, Model,
                                 DBLayerNotFound,
                                 DBLayerNoRiakObj,
                                 DBLayerException)


class M1(Model):

    f1 = Field(str)
    f2 = Field(int)
    f3 = Field(int, fname='some_field')

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


def test_normal_index(rk):
    key = next(rk)
    key2 = next(rk)

    m1 = M1.from_dict(key, {'f1': 'blah', 'f2': 150,
                            'ind': {'blah': 'something'}})
    m1.save()

    m2 = M1.from_dict(key2, {'f1': 'blah', 'f2': 150,
                            'ind': {'blah': 'something2'}})
    m2.save()
    assert M1.ind.filter('blah=somethi*') == set([key, key2])
    assert M1.ind.filter('blah=something') == set([key])
    assert M1.ind.filter('blah=something2') == set([key2])


