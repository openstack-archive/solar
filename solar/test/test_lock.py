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

from mock import patch
import pytest

from solar.dblayer.locking import Lock
from solar.dblayer.locking import Waiter
from solar.dblayer.model import clear_cache
from solar.dblayer.solar_models import Lock as DBLock


def test_acquire_release_logic():
    uid = '2131'
    first = '1111'
    second = '2222'
    assert Lock._acquire(uid, first, 'a').who_is_locking() == first
    clear_cache()
    assert Lock._acquire(uid, second, 'a').who_is_locking() == first
    Lock._release(uid, first, 'a')
    assert Lock._acquire(uid, second, 'a').who_is_locking() == second


def test_lock_acquired_released():
    uid = '11'
    with Lock(uid, uid, waiter=Waiter(1)):
        clear_cache()
        assert Lock._acquire(uid, '12', 'a').who_is_locking() == '11'
    assert Lock._acquire(uid, '12', 'a').who_is_locking() == '12'


def test_raise_error_if_acquired():
    uid = '11'
    Lock._acquire(uid, '12', 'a')
    clear_cache()
    with pytest.raises(RuntimeError):
        with Lock(uid, '13'):
            assert True


@patch('solar.dblayer.locking.Waiter.wait')
def test_time_sleep_called(msleep):
    uid = '11'
    Lock._acquire(uid, '12', 'a')
    clear_cache()
    sleep_time = 5
    with pytest.raises(RuntimeError):
        with Lock(uid, '13', 1, waiter=Waiter(sleep_time)):
            assert True
    msleep.assert_called_once_with(uid, '13')


def test_lock_released_exception():
    uid = '11'
    with pytest.raises(Exception):
        with Lock(uid, uid):
            raise Exception

    new_lock = Lock._acquire(uid, '12', 'a')
    assert new_lock.who_is_locking() == '12'


def test_locker_logic():
    uid = '11'
    l = DBLock.from_dict(uid, {})

    l.lockers = [['a', -1, 'x'], ['a', 1, 'y'], ['b', 1, 'z']]
    l.reduce()
    assert l.am_i_locking('b')
    l.who_is_locking() == 'b'
