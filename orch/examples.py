

import networkx as nx

from orch.tasks import *
from orch.graph import *


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


def ex1_exec():
    save_graph('current', ex1())
    schedule_next.apply()


def ex2():

    dg = nx.DiGraph()

    dg.add_node('rabbitmq_cluster2.join', type='cmd', args=['echo "joining"'], status='PENDING')
    dg.add_node('rabbitmq_cluster3.join', type='cmd', args=['echo "joining"'], status='PENDING')
    dg.add_node('rabbitmq_cluster.ready', type='anchor', args=[], status='PENDING')

    dg.add_edge('rabbitmq_cluster2.join', 'rabbitmq_cluster.ready')
    dg.add_edge('rabbitmq_cluster3.join', 'rabbitmq_cluster.ready')

    return dg

def ex2_exec():
    save_graph('current', ex2())
    schedule_start.apply_async()