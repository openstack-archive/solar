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

from dictdiffer import patch
from dictdiffer import revert
from pytest import fixture

from solar.system_log import change


@fixture
def staged():
    return {'ip': {'value': '10.0.0.2'},
            'list_val': {'value': [1, 2]}}


@fixture
def commited():
    return {'ip': '10.0.0.2',
            'list_val': [1]}


@fixture
def full_diff(staged):
    return change.create_diff(staged, {})


@fixture
def diff_for_update(staged, commited):
    return change.create_diff(staged, commited)


def test_create_diff_with_empty_commited(full_diff):
    operations = set()
    vals = {}
    for item in full_diff:
        operations.add(item[0])
        for val in item[2]:
            vals[val[0]] = val[1]

    assert len(full_diff) == 1
    assert set(['add']) == operations
    assert vals['ip'] == {'value': '10.0.0.2'}
    assert vals['list_val'] == {'value': [1, 2]}


def test_create_diff_modified(diff_for_update):
    operations = set()
    vals = {}
    for item in diff_for_update:
        operations.add(item[0])
        vals[item[1]] = item[2]

    assert len(diff_for_update) == 2
    assert set(['change']) == operations
    assert vals['ip'] == ('10.0.0.2', {'value': '10.0.0.2'})
    assert vals['list_val'] == ([1], {'value': [1, 2]})


def test_verify_patch_creates_expected(staged, diff_for_update, commited):
    expected = patch(diff_for_update, commited)
    assert expected == staged


def test_revert_update(staged, diff_for_update, commited):
    expected = revert(diff_for_update, staged)
    assert expected == commited
