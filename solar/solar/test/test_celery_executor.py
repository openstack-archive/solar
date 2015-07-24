
import networkx as nx
from pytest import fixture
from mock import patch

from solar.orchestration import executor


@fixture
def dg():
    ex = nx.DiGraph()
    ex.add_node('t1', args=['t'], status='PENDING', type='echo')
    ex.graph['uid'] = 'some_string'
    return ex


@patch.object(executor, 'app')
def test_celery_executor(mapp, dg):
    """Just check that it doesnt fail for now.
    """
    assert executor.celery_executor(dg, ['t1'])
    assert dg.node['t1']['status'] == 'INPROGRESS'
