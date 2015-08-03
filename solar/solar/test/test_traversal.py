

import networkx as nx
from pytest import fixture

from solar.orchestration.traversal import traverse

@fixture
def tasks():
    return [
        {'id': 't1', 'status': 'PENDING'},
        {'id': 't2', 'status': 'PENDING'},
        {'id': 't3', 'status': 'PENDING'},
        {'id': 't4', 'status': 'PENDING'},
        {'id': 't5', 'status': 'PENDING'}]

@fixture
def dg(tasks):
    ex = nx.DiGraph()
    for t in tasks:
        ex.add_node(t['id'], status=t['status'])
    return ex


def test_parallel(dg):
    dg.add_path(['t1', 't3', 't4', 't5'])
    dg.add_path(['t2', 't3'])

    assert set(traverse(dg)) == {'t1', 't2'}


def test_walked_only_when_all_predecessors_visited(dg):
    dg.add_path(['t1', 't3', 't4', 't5'])
    dg.add_path(['t2', 't3'])

    dg.node['t1']['status'] = 'SUCCESS'
    dg.node['t2']['status'] = 'INPROGRESS'

    assert set(traverse(dg)) == set()

    dg.node['t2']['status'] = 'SUCCESS'

    assert set(traverse(dg)) == {'t3'}


def test_nothing_will_be_walked_if_parent_is_skipped(dg):
    dg.add_path(['t1', 't2', 't3', 't4', 't5'])
    dg.node['t1']['status'] = 'SKIPPED'

    assert set(traverse(dg)) == set()

def test_node_will_be_walked_if_parent_is_noop(dg):
    dg.add_path(['t1', 't2', 't3', 't4', 't5'])
    dg.node['t1']['status'] = 'NOOP'

    assert set(traverse(dg)) == {'t2'}
