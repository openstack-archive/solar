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
    return {'id': 'res.1',
            'tags': ['res', 'node.1'],
            'input': {'ip': {'value': '10.0.0.2'},
                      'list_val': {'value': [1, 2]}},
            'metadata': {},
            'connections': [
                ['node.1', 'res.1', ['ip', 'ip']],
                ['node.1', 'res.1', ['key', 'key']]
            ]}



@fixture
def commited():
    return {'id': 'res.1',
            'tags': ['res', 'node.1'],
            'input': {'ip': '10.0.0.2',
                      'list_val': [1]},
            'metadata': {},
            'connections': [
                ['node.1', 'res.1', ['ip', 'ip']]
            ]}



@fixture
def full_diff(staged):
    return change.create_diff(staged, {})


@fixture
def diff_for_update(staged, commited):
    return change.create_diff(staged, commited)


def test_create_diff_with_empty_commited(full_diff):
    # add will be executed
    expected = [('add', '',
                 [('connections', [['node.1', 'res.1', ['ip', 'ip']],
                                   ['node.1', 'res.1', ['key', 'key']]]),
                  ('input', {
                      'ip': {'value': '10.0.0.2'},
                      'list_val': {'value': [1, 2]}
                  }), ('metadata', {}), ('id', 'res.1'),
                  ('tags', ['res', 'node.1'])])]
    assert full_diff == expected


def test_create_diff_modified(diff_for_update):
    assert diff_for_update == [
        ('add', 'connections', [(1, ['node.1', 'res.1', ['key', 'key']])]),
        ('change', 'input.ip',
         ('10.0.0.2', {'value': '10.0.0.2'})), ('change', 'input.list_val',
                                                ([1], {'value': [1, 2]}))
    ]


def test_verify_patch_creates_expected(staged, diff_for_update, commited):
    expected = patch(diff_for_update, commited)
    assert expected == staged


def test_revert_update(staged, diff_for_update, commited):
    expected = revert(diff_for_update, staged)
    assert expected == commited


@fixture
def resources():
    r = {'n.1': {'uid': 'n.1',
                 'args': {'ip': '10.20.0.2'},
                 'connections': [],
                 'tags': []},
         'r.1': {'uid': 'r.1',
                 'args': {'ip': '10.20.0.2'},
                 'connections': [['n.1', 'r.1', ['ip', 'ip']]],
                 'tags': []},
         'h.1': {'uid': 'h.1',
                 'args': {'ip': '10.20.0.2',
                          'ips': ['10.20.0.2']},
                 'connections': [['n.1', 'h.1', ['ip', 'ip']]],
                 'tags': []}}
    return r
