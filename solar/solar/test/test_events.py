
import networkx as nx
from pytest import fixture



@fixture
def simple():
    dg = nx.DiGraph()
    dg.add_edge('mariadb.run', 'keystone_config.run', event='changed')
    dg.add_edge('keystone_config.run', 'haproxy.reload', event='changed')
    return dg


def test_simple(simple):
    pass



@fixture
def rmq():
    """Example of a case when we have cycles on a data plane."""
    dg = nx.DiGraph()
    dg.add_edge('rmq_cluster.run', 'rmq_cluster.1.create', event='changed')
    dg.add_edge('rmq_cluster.run', 'rmq_cluster.2.join', event='changed')
    dg.add_edge('rmq_cluster.run', 'rmq_cluster.3.join', event='changed')
    dg.add_edge('rmq.1.run', 'rmq_cluster.1.create', event='changed')
    dg.add_edge('rmq.2.run', 'rmq_cluster.2.join', event='changed')
    dg.add_edge('rmq.3.run', 'rmq_cluster.3.join', event='changed')
    dg.add_edge('rmq_cluster.1.create', 'rmq_cluster.2.join', event='changed')
    dg.add_edge('rmq_cluster.1.create', 'rmq_cluster.3.join', event='changed')
    return dg


def test_rmq(rmq):
    pass


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
    pass
