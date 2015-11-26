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


__all__ = ['add_dep', 'add_react', 'Dep', 'React', 'add_event']

import networkx as nx

from solar.core.log import log
from solar.dblayer.solar_models import Resource
from solar.events.controls import Dep
from solar.events.controls import React



def create_event(event_dict):
    etype = event_dict['etype']
    kwargs = {'child': event_dict['child'],
              'parent': event_dict['parent'],
              'child_action': event_dict['child_action'],
              'parent_action': event_dict['parent_action'],
              'state': event_dict['state']}
    if etype == React.etype:
        return React(**kwargs)
    elif etype == Dep.etype:
        return Dep(**kwargs)
    else:
        raise Exception('No support for type %s', etype)


def add_default_events(emitter, receiver):
    events_to_add = [
        Dep(emitter.name, 'run', 'success', receiver.name, 'run'),
        Dep(emitter.name, 'update', 'success', receiver.name, 'update'),
        Dep(receiver.name, 'remove', 'success', emitter.name, 'remove')
    ]
    add_events(emitter.name, events_to_add)


def add_event(ev):
    rst = all_events(ev.parent)
    for rev in rst:
        if ev == rev:
            break
    else:
        add_events(ev.parent, [ev])


def add_dep(parent, dep, actions, state='success'):
    for act in actions:
        d = Dep(parent, act, state=state,
                child=dep, child_action=act)
        add_event(d)
        log.debug('Added event: %s', d)


def add_react(parent, dep, actions, state='success'):
    for act in actions:
        r = React(parent, act, state=state,
                  child=dep, child_action=act)
        add_event(r)
        log.debug('Added event: %s', r)


def add_events(resource, lst):
    resource = Resource.get(resource)
    events = resource.events
    # TODO: currently we don't track mutable objects
    events.extend([ev.to_dict() for ev in lst])
    resource.events = events
    # import pdb; pdb.settrace()
    resource.save_lazy()


def remove_event(ev):
    to_remove = ev.to_dict()
    resource = ev.parent
    resource = Resource.get(resource)
    # TODO: currently we don't track mutable objects
    events = resource.events
    events.remove(to_remove)
    resource.events = events
    resource.save_lazy()


def all_events(resource):
    return [create_event(e) for e in Resource.get(resource).events]


def bft_events_graph(start):
    """Builds graph of events traversing events in breadth-first order

    This graph doesnt necessary reflect deployment order, it is used
    to show dependencies between resources
    """
    dg = nx.DiGraph()
    stack = [start]
    visited = set()

    while stack:
        item = stack.pop()
        current_events = all_events(item)

        for ev in current_events:
            dg.add_edge(ev.parent_node, ev.child_node, label=ev.state)

            if ev.child in visited:
                continue

            # it is possible to have events leading to same resource but
            # different action
            if ev.child in stack:
                continue

            stack.append(ev.child)
        visited.add(ev.parent)
    return dg


def build_edges(changes_graph, events):
    """Builds graph edges

    :param changes_graph: nx.DiGraph object with actions to be executed
    :param events: {res: [controls.Event objects]}
    """
    events_graph = nx.MultiDiGraph()

    for res_evts in events.values():
        for ev in res_evts:
            events_graph.add_edge(ev.parent_node, ev.child_node, event=ev)

    stack = changes_graph.nodes()
    visited = set()
    while stack:
        event_name = stack.pop(0)

        if event_name in events_graph:
            log.debug('Next events after %s are %s', event_name,
                      events_graph.successors(event_name))
        else:
            log.debug('No outgoing events based on %s', event_name)

        if event_name not in visited:
            for parent, child, data in events_graph.edges(event_name,
                                                          data=True):
                succ_ev = data['event']
                succ_ev.insert(stack, changes_graph)
        visited.add(event_name)
    return changes_graph
