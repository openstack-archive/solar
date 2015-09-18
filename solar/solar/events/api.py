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
        resource_db = orm.DBResource.load(ev.parent)
        event_db = orm.DBEvent(**ev.to_dict())
        event_db.save()
        resource_db.events.add(event_db)


def add_dep(parent, dep, actions, state='success'):
    for act in actions:
        d = Dep(parent, act, state=state,
                depend_node=dep, depend_action=act)
        add_event(d)
        log.debug('Added event: %s', d)


def add_react(parent, dep, actions, state='success'):
    for act in actions:
        r = React(parent, act, state=state,
                  depend_node=dep, depend_action=act)
        add_event(r)
        log.debug('Added event: %s', r)


def add_events(resource, lst):
    db_resource = orm.DBResource.load(resource)
    for ev in lst:
        event_db = orm.DBEvent(**ev.to_dict())
        event_db.save()
        db_resource.events.add(event_db)


def set_events(resource, lst):
    db_resource = orm.DBResource.load(resource)
    for ev in db_resource.events.as_set():
        ev.delete()
    for ev in lst:
        event_db = orm.DBEvent(**ev.to_dict())
        event_db.save()
        db_resource.events.add(event_db)


def remove_event(ev):
    event_db = orm.DBEvent(**ev.to_dict())
    event_db.delete()


def all_events(resource):
    events = orm.DBResource.load(resource).events.as_set()

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
            dg.add_edge(ev.parent, ev.dependent, label=ev.state)

            if ev.depend_node in visited:
                continue

            # it is possible to have events leading to same resource but
            # different action
            if ev.depend_node in stack:
                continue

            stack.append(ev.depend_node)
        visited.add(ev.parent_node)
    return dg



def build_edges(changed_resources, changes_graph, events):
    """
    :param changed_resources: list of resource names that were changed
    :param changes_graph: nx.DiGraph object with actions to be executed
    :param events: {res: [controls.Event objects]}
    """
    stack = changed_resources[:]
    visited = []
    while stack:
        node = stack.pop()

        if node in events:
            log.debug('Events %s for resource %s', events[node], node)
        else:
            log.debug('No dependencies based on %s', node)

        if node not in visited:
            for ev in events.get(node, ()):
                ev.insert(stack, changes_graph)

        visited.append(node)
    return changes_graph
