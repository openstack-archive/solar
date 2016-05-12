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

import time
import uuid

from collections import Counter

import networkx as nx

from solar.dblayer.model import ModelMeta
from solar.dblayer.solar_models import Task
from solar import errors
from solar.orchestration.traversal import states
from solar import utils


def save_graph(graph):
    for n in nx.topological_sort(graph):
        values = {'name': n, 'execution': graph.graph['uid']}
        values.update(graph.node[n])
        t = Task.new(values)
        graph.node[n]['task'] = t
        for pred in graph.predecessors(n):
            pred_task = graph.node[pred]['task']
            t.parents.add(pred_task)
            pred_task.save()
        t.save_lazy()


def set_states(uid, tasks):
    plan = get_graph(uid)
    for t in tasks:
        if t not in plan.node:
            raise Exception("No task %s in plan %s", t, uid)
        plan.node[t].status = states.NOOP.name
        plan.node[t].save_lazy()


def get_task_by_name(dg, task_name):
    return next(t for t in dg.nodes() if t.name == task_name)


def get_graph(uid):
    mdg = nx.MultiDiGraph()
    mdg.graph['uid'] = uid
    mdg.graph['name'] = uid.split(':')[0]
    tasks_by_uid = {t.key: t for t
                    in Task.multi_get(Task.execution.filter(uid))}
    mdg.add_nodes_from(tasks_by_uid.values())
    mdg.add_edges_from([(tasks_by_uid[parent], task) for task in mdg.nodes()
                        for parent in task.parents.all()])
    return mdg


def longest_path_time(graph):
    """We are not interested in the path itself, just get the start
    of execution and the end of it.
    """
    start = float('inf')
    end = float('-inf')
    for n in graph:
        node_start = n.start_time
        node_end = n.end_time
        if int(node_start) == 0 or int(node_end) == 0:
            continue

        if node_start < start:
            start = node_start

        if node_end > end:
            end = node_end
    return max(end - start, 0.0)


def total_delta(graph):
    delta = 0.0
    for n in graph:
        node_start = n.start_time
        node_end = n.end_time
        if int(node_start) == 0 or int(node_end) == 0:
            continue
        delta += node_end - node_start
    return delta


get_plan = get_graph


def assign_weights_nested(dg):
    """Based on number of childs assign weights that will be
    used later for scheduling.
    """
    #: NOTE reverse(copy=False) swaps successors and predecessors
    # on same copy of graph, thus before returning it - reverse it back
    reversed_graph = dg.reverse(copy=False)
    for task in nx.topological_sort(reversed_graph):
        task.weight = sum([t.weight + 1 for t
                           in reversed_graph.predecessors(task)])
        task.save_lazy()
    return reversed_graph.reverse(copy=False)


def parse_plan(plan_path):
    """parses yaml definition and returns graph"""
    plan = utils.yaml_load(plan_path)
    dg = nx.MultiDiGraph()
    dg.graph['name'] = plan['name']
    for task in plan['tasks']:
        defaults = {
            'status': 'PENDING',
            'errmsg': '',
        }
        defaults.update(task['parameters'])
        dg.add_node(
            task['uid'], **defaults)
        for v in task.get('before', ()):
            dg.add_edge(task['uid'], v)
        for u in task.get('after', ()):
            dg.add_edge(u, task['uid'])
    return dg


def create_plan_from_graph(dg):
    dg.graph['uid'] = "{0}:{1}".format(dg.graph['name'], str(uuid.uuid4()))
    # FIXME change save_graph api to return new graph with Task objects
    # included
    save_graph(dg)
    ModelMeta.save_all_lazy()
    return get_graph(dg.graph['uid'])


def show(uid):
    dg = get_graph(uid)
    result = {}
    tasks = []
    result['uid'] = dg.graph['uid']
    result['name'] = dg.graph['name']
    for task in nx.topological_sort(dg):
        tasks.append(
            {'uid': task.name,
             'parameters': task.to_dict(),
             'before': dg.successors(task),
             'after': dg.predecessors(task)
             })
    result['tasks'] = tasks
    return utils.yaml_dump(result)


def create_plan(plan_path):
    return create_plan_from_graph(parse_plan(plan_path))


def reset_by_uid(uid, state_list=None):
    dg = get_graph(uid)
    return reset(dg, state_list=state_list)


def reset(graph, state_list=None):
    for n in graph:
        if state_list is None or n.status in state_list:
            n.status = states.PENDING.name
            n.start_time = 0.0
            n.end_time = 0.0
            n.save_lazy()


def reset_filtered(uid):
    reset_by_uid(uid, state_list=[states.SKIPPED.name, states.NOOP.name])


def report_progress(uid):
    return report_progress_graph(get_graph(uid))


def report_progress_graph(dg):
    tasks = []
    report = {
        'total_time': longest_path_time(dg),
        'total_delta': total_delta(dg),
        'tasks': tasks}

    # FIXME just return topologically sorted list of tasks
    for task in nx.topological_sort(dg):
        tasks.append([
            task.name,
            task.status,
            task.errmsg,
            task.start_time,
            task.end_time])

    return report


def wait_finish(uid, timeout):
    """Check if graph is finished

    Will return when no PENDING or INPROGRESS otherwise yields summary
    """
    start_time = time.time()

    while start_time + timeout >= time.time():
        dg = get_graph(uid)
        summary = Counter()
        summary.update({s.name: 0 for s in states})
        summary.update([task.status for task in dg.nodes()])
        yield summary
        if summary[states.PENDING.name] + summary[states.INPROGRESS.name] == 0:
            return
        else:
            # on db backends with snapshot isolation level and higher
            # updates wont be visible after start of transaction,
            # in order to report state correctly we will "refresh" transcation
            ModelMeta.session_end()
            ModelMeta.session_start()

    else:
        raise errors.ExecutionTimeout(
            'Run %s wasnt able to finish' % uid)
