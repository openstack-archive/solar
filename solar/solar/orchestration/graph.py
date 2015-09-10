

import json
import uuid

import networkx as nx
import yaml

from solar import utils


from solar.interfaces.db import get_db

db = get_db()


def save_graph(name, graph):
    # maybe it is possible to store part of information in AsyncResult backend
    uid = graph.graph['uid']
    db.create(uid, graph.graph, db.COLLECTIONS.plan_graph)

    for n in graph:
        collection = db.COLLECTIONS.plan_node.name + ':' + uid
        db.create(n, properties=graph.node[n], collection=collection)
        db.create_relation_str(uid, n, type_=db.RELATION_TYPES.graph_to_node)

    for u, v, properties in graph.edges(data=True):
        type_ = db.RELATION_TYPES.plan_edge.name + ':' + uid
        db.create_relation_str(u, v, properties, type_=type_)


def get_graph(uid):
    dg = nx.MultiDiGraph()
    collection = db.COLLECTIONS.plan_node.name + ':' + uid
    type_= db.RELATION_TYPES.plan_edge.name + ':' + uid
    dg.graph = db.get(uid, collection=db.COLLECTIONS.plan_graph).properties
    dg.add_nodes_from([(n.uid, n.properties) for n in db.all(collection=collection)])
    dg.add_edges_from([(i['source'], i['dest'], i['properties']) for
                       i in db.all_relations(type_=type_, db_convert=False)])
    return dg


get_plan = get_graph


def parse_plan(plan_data):
    """ parses yaml definition and returns graph
    """
    plan = yaml.load(plan_data)
    dg = nx.MultiDiGraph()
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


def report_topo(uid):

    dg = get_graph(uid)
    report = []

    for task in nx.topological_sort(dg):
        report.append([task, dg.node[task]['status'], dg.node[task]['errmsg']])

    return report
