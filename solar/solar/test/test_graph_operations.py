
from pytest import fixture
from pytest import mark
import networkx as nx

from solar.orchestration import graph
from solar.orchestration import filters


@fixture
def dg_ex1():
    dg = nx.DiGraph()
    dg.add_nodes_from(['n1', 'n2', 'n3', 'n4', 'n5'])
    dg.add_path(['n1', 'n5'])
    dg.add_path(['n3', 'n5'])
    dg.add_path(['n1', 'n2','n4'])
    return dg


@mark.parametrize("end_nodes,visited", [
    (['n5'], {'n1', 'n3', 'n5'}),
    (['n4'], {'n1', 'n2', 'n4'}),
    (['n4', 'n5'], {'n1', 'n2', 'n3', 'n4', 'n5'}),
])
def test_end_at(dg_ex1, end_nodes, visited):
    assert set(filters.end_at(dg_ex1, end_nodes).nodes()) == visited

@mark.parametrize("start_nodes,visited", [
    (['n3'], {'n3', 'n5'}),
    (['n1'], {'n1', 'n2', 'n4','n5'}),
])
def test_start_from(dg_ex1, start_nodes, visited):
    assert set(filters.start_from(dg_ex1, start_nodes).nodes()) == visited

@fixture
def dg_ex2():
    dg = nx.DiGraph()
    dg.add_nodes_from(['n1', 'n2', 'n3', 'n4', 'n5'])
    dg.add_edges_from([('n1', 'n3'), ('n2', 'n3'), ('n3', 'n4'), ('n3', 'n5')])
    return dg

@mark.parametrize("start_nodes,visited", [
    (['n3'], {'n1', 'n2'}),
    (['n4'], {'n1', 'n2', 'n3', 'n5'},),
    (['n2'], {'n1', 'n3', 'n4', 'n5'},)
])
def test_exclude_path(dg_ex2, start_nodes, visited):
    assert set(filters.exclude_paths(dg_ex2, start_nodes).nodes()) == visited