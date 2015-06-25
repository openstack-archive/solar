

import networkx as nx

from orch.tasks import *
from orch.graph import *

from pytest import fixture

import time


@fixture(autouse=True)
def clean_ignored():
    r.delete('tasks.ignore')


def ex1():
    dg = nx.DiGraph()

    dg.add_node('rabbitmq_cluster1.create', type='cmd', args=['echo "installing cluster"'], status='PENDING')
    dg.add_node('rabbitmq_cluster2.join', type='cmd', args=['echo "joining"'], status='PENDING')
    dg.add_node('rabbitmq_cluster3.join', type='cmd', args=['echo "joining"'], status='PENDING')
    dg.add_node('rabbitmq_cluster.ready', type='anchor', args=[], status='PENDING')

    dg.add_edge('rabbitmq_cluster1.create', 'rabbitmq_cluster2.join')
    dg.add_edge('rabbitmq_cluster1.create', 'rabbitmq_cluster3.join')
    dg.add_edge('rabbitmq_cluster1.create', 'rabbitmq_cluster.ready')
    dg.add_edge('rabbitmq_cluster2.join', 'rabbitmq_cluster.ready')
    dg.add_edge('rabbitmq_cluster3.join', 'rabbitmq_cluster.ready')

    dg.add_node('compute1', type='cmd', args=['echo "compute1"'], status='PENDING')
    dg.add_node('compute2', type='cmd', args=['echo "compute2"'], status='PENDING')
    dg.add_node('compute3', type='cmd', args=['echo "compute3"'], status='PENDING')
    dg.add_node('compute4', type='error', args=['echo "compute4"'], status='PENDING')
    dg.add_node('compute5', type='error', args=['echo "compute5"'], status='PENDING')
    dg.add_node('compute_ready', type='fault_tolerance', args=[60], status='PENDING')

    dg.add_edge('rabbitmq_cluster.ready', 'compute1')
    dg.add_edge('rabbitmq_cluster.ready', 'compute2')
    dg.add_edge('rabbitmq_cluster.ready', 'compute3')
    dg.add_edge('rabbitmq_cluster.ready', 'compute4')
    dg.add_edge('rabbitmq_cluster.ready', 'compute5')

    dg.add_edge('compute1', 'compute_ready')
    dg.add_edge('compute2', 'compute_ready')
    dg.add_edge('compute3', 'compute_ready')
    dg.add_edge('compute4', 'compute_ready')
    dg.add_edge('compute5', 'compute_ready')

    return dg


def test_ex1_exec():
    save_graph('current', ex1())
    schedule_start.apply_async(queue='master')


def ex2():

    dg = nx.DiGraph()

    dg.add_node('rabbitmq_cluster2.join', type='cmd', args=['echo "joining"'], status='PENDING')
    dg.add_node('rabbitmq_cluster3.join', type='cmd', args=['echo "joining"'], status='PENDING')
    dg.add_node('rabbitmq_cluster.ready', type='anchor', args=[], status='PENDING')

    dg.add_edge('rabbitmq_cluster2.join', 'rabbitmq_cluster.ready')
    dg.add_edge('rabbitmq_cluster3.join', 'rabbitmq_cluster.ready')

    return dg

def test_ex2_exec():
    save_graph('current', ex2())
    schedule_start.apply_async(queue='master')


def test_timelimit_exec():

    dg = nx.DiGraph()

    dg.add_node(
        'timelimit_test', type='sleep',
        args=[100], status='PENDING',
        time_limit=10)

    dg.add_node(
        'soft_timelimit_test', type='sleep',
        args=[100], status='PENDING',
        soft_time_limit=10)

    save_graph('current', dg)
    schedule_start.apply_async(queue='master')


def test_timeout():
    # TODO(dshulyak) how to handle connectivity issues?
    # or hardware failure ?
    dg = nx.DiGraph()

    dg.add_node(
        'test_timeout', type='echo', target='unreachable',
        args=['yoyoyo'], status='PENDING',
        timeout=1)

    save_graph('current', dg)
    # two tasks will be fired - test_timeout and fire_timeout(test_timeout)
    # with countdown set to 10 sec
    schedule_start.apply_async(queue='master')
    # after 10 seconds fire_timeout will set test_timeout to ERROR
    time.sleep(1)

    # master host will start listening from unreachable queue, but task will be ignored
    # e.g it will be acked, and fetched from broker, but not processed
    assert app.control.add_consumer(
                'unreachable', reply=True, destination=['celery@master'])
    dg = get_graph('current')
    assert dg.node['test_timeout']['status'] == 'ERROR'



def test_target_exec():
    dg = nx.DiGraph()

    dg.add_node(
        'vagrant_reload', type='cmd',
        args=['vagrant reload solar-dev1'], status='PENDING', target='ipmi')
    save_graph('current', dg)
    schedule_start.apply_async(queue='master')


def test_limit_concurrency():
    # - no more than 2 tasks in general
    dg = nx.DiGraph()
    dg.graph['concurrency'] = 2

    for i in range(4):
        dg.add_node(
            str(i), type='echo',
            args=[i], status='PENDING')

    save_graph('current', dg)
    schedule_start.apply_async(queue='master')


def test_ignored():

    dg = nx.DiGraph()

    dg.add_node(
        'test_ignored', type='echo', args=['hello'], status='PENDING')
    r.sadd('tasks.ignore', 'test_ignored')
    save_graph('current', dg)

    schedule_start.apply_async(queue='master')
    ignored = app.AsyncResult('test_ignored')
    ignored.get()
    dg = get_graph('current')
    assert dg.node['test_ignored']['status'] == {}
