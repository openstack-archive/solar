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


def test_acquire_release_logic():
    uid = '2131'
    first = '1111'
    second = '2222'
    assert Lock._acquire(uid, first).identity == first
    assert Lock._acquire(uid, second).identity == first
    Lock._release(uid)
    assert Lock._acquire(uid, second).identity == second


def test_lock_acquired_released():
    uid = '11'
    with Lock(uid, uid):
        assert Lock._acquire(uid, '12').identity == '11'
    assert Lock._acquire(uid, '12').identity == '12'


def test_raise_error_if_acquired():
    uid = '11'
    Lock._acquire(uid, '12')
    with pytest.raises(RuntimeError):
        with Lock(uid, '13'):
            assert True


@patch('solar.dblayer.locking.time.sleep')
def test_time_sleep_called(msleep):
    uid = '11'
    Lock._acquire(uid, '12')
    sleep_time = 5
    with pytest.raises(RuntimeError):
        with Lock(uid, '13', 1, sleep_time):
            assert True
    msleep.assert_called_once_with(sleep_time)


def test_lock_released_exception():
    uid = '11'
    with pytest.raises(Exception):
        with Lock(uid, uid):
            raise Exception

    new_lock = Lock._acquire(uid, '12')
    assert new_lock.identity == '12'
