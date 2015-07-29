

from pytest import fixture
import networkx as nx

from solar.orchestration import limits


@fixture
def dg():
    ex = nx.DiGraph()
    ex.add_node('t1', status='PENDING', target='1',
                resource_type='node', type_limit=2)
    ex.add_node('t2', status='PENDING', target='1',
                resource_type='node', type_limit=2)
    ex.add_node('t3', status='PENDING', target='1',
                resource_type='node', type_limit=2)
    return ex


def test_target_rule(dg):

    assert limits.target_based_rule(dg, [], 't1') == True
    assert limits.target_based_rule(dg, ['t1'], 't2') == False


def test_type_limit_rule(dg):
    assert limits.type_based_rule(dg, ['t1'], 't2') == True
    assert limits.type_based_rule(dg, ['t1', 't2'], 't3') == False


def test_items_rule(dg):

    assert limits.items_rule(dg, ['1']*99, '2')
    assert limits.items_rule(dg, ['1']*99, '2', limit=10) == False


@fixture
def target_dg():
    ex = nx.DiGraph()
    ex.add_node('t1', status='PENDING', target='1')
    ex.add_node('t2', status='PENDING', target='1')

    return ex


def test_filtering_chain(target_dg):

    chain = limits.get_default_chain(target_dg, [], ['t1', 't2'])
    assert list(chain) == ['t1']
