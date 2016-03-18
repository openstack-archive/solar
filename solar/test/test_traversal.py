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

from mock import Mock
import networkx as nx
from pytest import fixture

from solar.orchestration.traversal import find_visitable_tasks


@fixture
def task():
    number = {'count': 0}

    def make_task():
        number['count'] += 1
        return Mock(name='t%s' % number, status='PENDING')
    return make_task


@fixture
def t1(task):
    return task()


@fixture
def t2(task):
    return task()


@fixture
def t3(task):
    return task()


@fixture
def t4(task):
    return task()


@fixture
def t5(task):
    return task()


@fixture
def dg(t1, t2, t3, t4, t5):
    ex = nx.DiGraph()
    ex.add_nodes_from((t1, t2, t3, t4, t5))
    return ex


def test_parallel(dg, t1, t2, t3, t4, t5):
    dg.add_path([t1, t3, t4, t5])
    dg.add_path([t2, t3])

    assert set(find_visitable_tasks(dg)) == {t1, t2}


def test_walked_only_when_all_predecessors_visited(dg, t1, t2, t3, t4, t5):
    dg.add_path([t1, t3, t4, t5])
    dg.add_path([t2, t3])

    t1.status = 'SUCCESS'
    t2.status = 'INPROGRESS'

    assert set(find_visitable_tasks(dg)) == set()

    t2.status = 'SUCCESS'

    assert set(find_visitable_tasks(dg)) == {t3}


def test_nothing_will_be_walked_if_parent_is_skipped(dg, t1, t2, t3, t4, t5):
    dg.add_path([t1, t2, t3, t4, t5])
    t1.status = 'SKIPPED'

    assert set(find_visitable_tasks(dg)) == set()


def test_node_will_be_walked_if_parent_is_noop(dg, t1, t2, t3, t4, t5):
    dg.add_path([t1, t2, t3, t4, t5])
    t1.status = 'NOOP'

    assert set(find_visitable_tasks(dg)) == {t2}
