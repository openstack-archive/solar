#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import uuid
import time

import networkx as nx

from solar import utils
from .traversal import states
from solar import errors

from collections import Counter


from solar.interfaces.db import get_db

db = get_db()


def save_graph(graph):
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
    type_ = db.RELATION_TYPES.plan_edge.name + ':' + uid
    dg.graph = db.get(uid, collection=db.COLLECTIONS.plan_graph).properties
    dg.add_nodes_from([(n.uid, n.properties) for n in db.all(collection=collection)])
    dg.add_edges_from([(i['source'], i['dest'], i['properties'])
                       for i in db.all_relations(type_=type_, db_convert=False)])
    return dg


get_plan = get_graph


def parse_plan(plan_path):
    """ parses yaml definition and returns graph
    """
    plan = utils.yaml_load(plan_path)
    dg = nx.MultiDiGraph()
    dg.graph['name'] = plan['name']
    for task in plan['tasks']:
        defaults = {
            'status': 'PENDING',
            'errmsg': None,
            }
        defaults.update(task['parameters'])
        dg.add_node(
            task['uid'], **defaults)
        for v in task.get('before', ()):
            dg.add_edge(task['uid'], v)
        for u in task.get('after', ()):
            dg.add_edge(u, task['uid'])
    return dg


def create_plan_from_graph(dg, save=True):
    dg.graph['uid'] = "{0}:{1}".format(dg.graph['name'], str(uuid.uuid4()))
    if save:
        save_graph(dg)
    return dg


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


def create_plan(plan_path, save=True):
    """
    """
    dg = parse_plan(plan_path)
    return create_plan_from_graph(dg, save=save)


def update_plan(uid, plan_path):
    """update preserves old status of tasks if they werent removed
    """

    new = parse_plan(plan_path)
    old = get_graph(uid)
    return update_plan_from_graph(new, old).graph['uid']


def update_plan_from_graph(new, old):
    new.graph = old.graph
    for n in new:
        if n in old:
            new.node[n]['status'] = old.node[n]['status']

    save_graph(new)
    return new


def reset_by_uid(uid, state_list=None):
    dg = get_graph(uid)
    return reset(dg, state_list=state_list)


def reset(graph, state_list=None):
    for n in graph:
        if state_list is None or graph.node[n]['status'] in state_list:
            graph.node[n]['status'] = states.PENDING.name
    save_graph(graph)


def reset_filtered(uid):
    reset_by_uid(uid, state_list=[states.SKIPPED.name, states.NOOP.name])


def report_topo(uid):

    dg = get_graph(uid)
    report = []

    for task in nx.topological_sort(dg):
        data = dg.node[task]
        report.append([
            task,
            data['status'],
            data['errmsg'],
            data.get('start_time'),
            data.get('end_time')])

    return report


def wait_finish(uid, timeout):
    """Wait finish will periodically load graph and check if there is no
    PENDING or INPROGRESS
    """
    start_time = time.time()

    while start_time + timeout >= time.time():
        dg = get_graph(uid)
        summary = Counter()
        summary.update({s.name: 0 for s in states})
        summary.update([s['status'] for s in dg.node.values()])
        yield summary
        if summary[states.PENDING.name] + summary[states.INPROGRESS.name] == 0:
            return
    else:
        raise errors.ExecutionTimeout(
            'Run %s wasnt able to finish' % uid)
