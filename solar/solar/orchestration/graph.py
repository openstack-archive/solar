

import json
import uuid

import networkx as nx
import redis
import yaml

from solar import utils


r = redis.StrictRedis(host='10.0.0.2', port=6379, db=1)


def save_graph(name, graph):
    # maybe it is possible to store part of information in AsyncResult backend
    r.set('{}:nodes'.format(name), json.dumps(graph.node.items()))
    r.set('{}:edges'.format(name), json.dumps(graph.edges(data=True)))
    r.set('{}:attributes'.format(name), json.dumps(graph.graph))


def get_graph(name):
    dg = nx.DiGraph()
    nodes = json.loads(r.get('{}:nodes'.format(name)))
    edges = json.loads(r.get('{}:edges'.format(name)))
    dg.graph = json.loads(r.get('{}:attributes'.format(name)))
    dg.add_nodes_from(nodes)
    dg.add_edges_from(edges)
    return dg


get_plan = get_graph


def parse_plan(plan_data):
    """ parses yaml definition and returns graph
    """
    plan = yaml.load(plan_data)
    dg = nx.DiGraph()
    dg.graph['name'] = plan['name']
    for task in plan['tasks']:
        dg.add_node(
            task['uid'], status='PENDING', errmsg=None, **task['parameters'])
        for v in task.get('before', ()):
            dg.add_edge(task['uid'], v)
        for u in task.get('after', ()):
            dg.add_edge(u, task['uid'])
    return dg


def create_plan_from_graph(dg):
    dg.graph['uid'] = "{0}:{1}".format(dg.graph['name'], str(uuid.uuid4()))
    save_graph(dg.graph['uid'], dg)
    return dg.graph['uid']


def show(uid):
    dg = get_graph(uid)
    result = {}
    tasks = []
    result['uid'] = dg.graph['uid']
    result['name'] = dg.graph['name']
    for n in nx.topological_sort(dg):
        data = dg.node[n]
        tasks.append(
            {'uid': n,
             'parameters': data,
             'before': dg.successors(n),
             'after': dg.predecessors(n)
             })
    result['tasks'] = tasks
    return utils.yaml_dump(result)


def create_plan(plan_data):
    """
    """
    dg = parse_plan(plan_data)
    return create_plan_from_graph(dg)


def update_plan(uid, plan_data):
    """update preserves old status of tasks if they werent removed
    """
    dg = parse_plan(plan_data)
    old_dg = get_graph(uid)
    dg.graph = old_dg.graph
    for n in dg:
        if n in old_dg:
            dg.node[n]['status'] = old_dg.node[n]['status']

    save_graph(uid, dg)
    return uid


def reset(uid, states=None):
    dg = get_graph(uid)
    for n in dg:
        if states is None or dg.node[n]['status'] in states:
            dg.node[n]['status'] = 'PENDING'
    save_graph(uid, dg)


def soft_stop(uid):
    """Graph will stop when all currently inprogress tasks will be finished
    """
    dg = get_graph(uid)
    dg.graph['stop'] = True
    save_graph(uid, dg)


def report_topo(uid):

    dg = get_graph(uid)
    report = []

    for task in nx.topological_sort(dg):
        report.append([task, dg.node[task]['status'], dg.node[task]['errmsg']])

    return report
