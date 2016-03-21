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
from solar.dblayer.solar_models import HistoryItem
from solar.dblayer.solar_models import NegativeCounter


def test_composite_filter():

    l1 = HistoryItem.new('a', {'log': 'history', 'resource': 'a'})
    l2 = HistoryItem.new('b', {'log': 'history', 'resource': 'b'})

    l1.save()
    l2.save()
    assert HistoryItem.composite.filter({'log': 'history',
                                         'resource': 'a'}) == [l1.key]
    assert HistoryItem.composite.filter({'log': 'history',
                                         'resource': 'b'}) == [l2.key]


def test_negative_counter():
    nc = NegativeCounter.get_or_create('non_exist')
    assert nc.count == 0


def test_reversed_order_is_preserved():
    added = []
    for i in range(4):
        li = HistoryItem.new(str(i), {})
        li.save()
        added.append(li.key)
    added.reverse()
    assert list(HistoryItem.history.filter(StrInt.n_max(),
                                           StrInt.n_min(),
                                           max_results=2)) == added[:2]
