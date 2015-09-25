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


__all__ = ['add_dep', 'add_react']

import networkx as nx

from solar.core.log import log
from solar.interfaces import orm
from solar.events.controls import Dep, React, StateChange


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


def add_event(ev):
    rst = all_events(ev.parent)
    for rev in rst:
        if ev == rev:
            break
    else:
        rst.append(ev)
        resource_events = orm.DBResourceEvents.get_or_create(ev.parent)
        event_db = orm.DBEvent(**ev.to_dict())
        event_db.save()
        resource_events.events.add(event_db)


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
    resource_events = orm.DBResourceEvents.get_or_create(resource)
    for ev in lst:
        event_db = orm.DBEvent(**ev.to_dict())
        event_db.save()
        resource_events.events.add(event_db)


def set_events(resource, lst):
    resource_events = orm.DBResourceEvents.get_or_create(resource)
    for ev in db_resource.events.as_set():
        ev.delete()
    for ev in lst:
        event_db = orm.DBEvent(**ev.to_dict())
        event_db.save()
        resource_events.events.add(event_db)


def remove_event(ev):
    event_db = orm.DBEvent(**ev.to_dict())
    event_db.delete()


def all_events(resource):
    events = orm.DBResourceEvents.get_or_create(resource).events.as_set()

    if not events:
        return []
    return [create_event(i.to_dict()) for i in events]


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
    """
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
            log.debug('Next events after %s are %s', event_name, events_graph.successors(event_name))
        else:
            log.debug('No outgoing events based on %s', event_name)

        if event_name not in visited:
            for parent, child, data in events_graph.edges(event_name, data=True):
                succ_ev = data['event']
                succ_ev.insert(stack, changes_graph)

        visited.add(event_name)
    return changes_graph
