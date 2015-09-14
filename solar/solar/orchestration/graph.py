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

import json
import uuid

import networkx as nx
import redis

from solar import utils
from .traversal import states


r = redis.StrictRedis(host='10.0.0.2', port=6379, db=1)


def save_graph(name, graph):
    # maybe it is possible to store part of information in AsyncResult backend
    r.set('{}:nodes'.format(name), json.dumps(graph.node.items()))
    r.set('{}:edges'.format(name), json.dumps(graph.edges(data=True)))
    r.set('{}:attributes'.format(name), json.dumps(graph.graph))


def get_graph(name):
    dg = nx.OrderedMultiDiGraph()
    nodes = json.loads(r.get('{}:nodes'.format(name)))
    edges = json.loads(r.get('{}:edges'.format(name)))
    dg.graph = json.loads(r.get('{}:attributes'.format(name)))
    dg.add_nodes_from(nodes)
    dg.add_edges_from(edges)
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
        save_graph(dg.graph['uid'], dg)
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
    dg = parse_plan(plan_path)
    old_dg = get_graph(uid)
    dg.graph = old_dg.graph
    for n in dg:
        if n in old_dg:
            dg.node[n]['status'] = old_dg.node[n]['status']

    save_graph(uid, dg)
    return uid


def reset(uid, state_list=None):
    dg = get_graph(uid)
    for n in dg:
        if state_list is None or dg.node[n]['status'] in state_list:
            dg.node[n]['status'] = states.PENDING.name
    save_graph(uid, dg)


def reset_filtered(uid):
    reset(uid, state_list=[states.SKIPPED.name, states.NOOP.name])


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
