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

from solar.dblayer.model import StrInt
from solar.dblayer.solar_models import LogItem
from solar.dblayer.solar_models import NegativeCounter


def test_separate_logs():

    history = 'history'
    staged = 'staged'
    history_uids = set()
    staged_uids = set()
    for i in range(2):
        l = LogItem.new({'log': history})
        l.save()
        history_uids.add(l.key)
    for i in range(3):
        l = LogItem.new({'log': staged})
        l.save()
        staged_uids.add(l.key)

    assert set(LogItem.composite.filter({'log': history})) == history_uids
    assert set(LogItem.composite.filter({'log': staged})) == staged_uids


def test_multiple_filter():

    l1 = LogItem.new({'log': 'history', 'resource': 'a'})
    l2 = LogItem.new({'log': 'history', 'resource': 'b'})

    l1.save()
    l2.save()
    assert LogItem.composite.filter({'log': 'history',
                                     'resource': 'a'}) == [l1.key]
    assert LogItem.composite.filter({'log': 'history',
                                     'resource': 'b'}) == [l2.key]


def test_changed_index():

    l = LogItem.new({'log': 'staged', 'resource': 'a', 'action': 'run'})
    l.save()

    assert LogItem.composite.filter({'log': 'staged'}) == [l.key]

    l.log = 'history'
    l.save()

    assert LogItem.composite.filter({'log': 'staged'}) == []
    assert LogItem.composite.filter({'log': 'history'}) == [l.key]


def test_negative_counter():
    nc = NegativeCounter.get_or_create('non_exist')
    assert nc.count == 0


def test_reversed_order_is_preserved():
    added = []
    for i in range(4):
        li = LogItem.new({'log': 'history'})
        li.save()
        added.append(li.key)
    added.reverse()
    assert list(LogItem.history.filter(StrInt.n_max(),
                                       StrInt.n_min(),
                                       max_results=2)) == added[:2]


def test_staged_not_indexed():
    added = []
    for i in range(3):
        li = LogItem.new({'log': 'staged'})
        li.save()
        added.append(li)

    for li in added[:2]:
        li.log = 'history'
        li.save()

    assert set(LogItem.history.filter(StrInt.n_max(), StrInt.n_min())) == {
        li.key
        for li in added[:2]
    }


def test_history_last_filter():
    for i in range(4):
        li = LogItem.new({'log': 'history'})
        li.save()
        last = li

    assert LogItem.history_last() == last


def test_history_last_returns_none():
    assert LogItem.history_last() is None
