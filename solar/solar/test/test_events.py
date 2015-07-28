
import networkx as nx
from pytest import fixture


@fixture
def simple():
    dg = nx.DiGraph()
    dg.add_edge('mariadb.run', 'keystone_config.run', event='changed')
    dg.add_edge('keystone_config.run', 'haproxy.reload', event='changed')
    return dg

def test_simple(simple):
    nx.write_dot(simple, 'simple.dot')


@fixture
def rmq():
    """Example of a case when we have cycles on a data plane."""
    dg = nx.DiGraph()
    dg.add_edge('rmq.1.run', 'rmq.1.cluster_create', event='changed')
    dg.add_edge('rmq.1.cluster_create', 'rmq.2.cluster_join', event='changed')
    dg.add_edge('rmq.1.cluster_create', 'rmq.3.cluster_join', event='changed')
    dg.add_edge('rmq.2.run', 'rmq.2.cluster_join', event='changed')
    dg.add_edge('rmq.3.run', 'rmq.3.cluster_join', event='changed')
    return dg


def test_rmq(rmq):
    nx.write_dot(rmq, 'rmq.dot')


@fixture
def haproxy():
    """Example when we have cycles on a execution plane."""
    dg = nx.DiGraph()
    dg.add_edge('k', 'kc', event='changed')
    dg.add_edge('kc', 'ha', event='changed')
    dg.add_edge('g', 'gc', event='changed')
    dg.add_edge('gc', 'ha', event='changed')
    dg.add_edge('ha', 'gc', event='changed')
    return dg


def test_haproxy(haproxy):
    nx.write_dot(haproxy, 'haproxy.dot')
