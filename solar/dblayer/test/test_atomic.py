#    Copyright 2016 Mirantis, Inc.
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

from solar.dblayer.model import DBLayerException
from solar.dblayer.model import DBLayerNotFound
from solar.dblayer.model import Field
from solar.dblayer.model import Model
from solar.dblayer.model import ModelMeta
from solar.dblayer import utils


class T1(Model):

    fi1 = Field(str)


def save_multiple(key1, key2):
    ex1 = T1.from_dict({'key': key1, 'fi1': 'blah blah live'})
    ex1.save_lazy()
    ex2 = T1.from_dict({'key': key2, 'fi1': 'blah blah another live'})
    ex2.save_lazy()

atomic_save_multiple = utils.atomic(save_multiple)


def test_one_will_be_saved(rk):
    key = next(rk)
    with pytest.raises(DBLayerException):
        save_multiple(key, key)
        ModelMeta.session_end()

    assert T1.get(key)


def test_atomic_none_saved(rk):
    key = next(rk)

    with pytest.raises(DBLayerException):
        with utils.Atomic():
            save_multiple(key, key)

    with pytest.raises(DBLayerNotFound):
        assert T1.get(key)


def test_atomic_decorator_none_saved(rk):
    key = next(rk)

    with pytest.raises(DBLayerException):
        atomic_save_multiple(key, key)

    with pytest.raises(DBLayerNotFound):
        assert T1.get(key)


def test_atomic_save_all(rk):
    key1, key2 = (next(rk) for _ in range(2))
    atomic_save_multiple(key1, key2)
    assert T1.get(key1)
    assert T1.get(key2)


def test_atomic_helper_validation(rk):
    key1, key2, key3 = (next(rk) for _ in range(3))
    ex1 = T1.from_dict({'key': key1, 'fi1': 'stuff'})
    ex1.save_lazy()
    with pytest.raises(DBLayerException):
        atomic_save_multiple(key1, key2)
