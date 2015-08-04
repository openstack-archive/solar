

__all__ = ['add_event', 'remove_event', 'all_events', 'set_events']

import networkx as nx

from solar.interfaces.db import get_db
from solar.events.control import build_edges, Dependency, React

db = get_db()



def create_event(event_dict):
    etype = event_dict.pop('etype')
    if etype == React.etype:
        return React(**event_dict)
    elif etype == Dependency.etype:
        return Dependency(**event_dict)
    else:
        raise Exception('No support for type %s', etype)


def add_event(ev):
    rst = all_events(ev.parent_node)
    for rev in rst:
        if ev == rev:
            break
    else:
        rst.append(ev)
        db.save(
            ev.parent_node,
            [i.to_dict() for i in rst],
            collection=db.COLLECTIONS.events)

def remove_event(ev):
    rst = all_events(ev.parent_node)
    db.save(
        ev.parent_node,
        [i.to_dict() for i in rst],
        collection=db.COLLECTIONS.events)

def set_events(resource, lst):
    db.save(
        resource,
        [i.to_dict() for i in lst],
        collection=db.COLLECTIONS.events)


def add_events(resource, lst):
    rst = all_events(resource)
    rst.extend(lst)
    set_events(resource, rst)


def all_events(resource):
    events = db.read(resource, collection=db.COLLECTIONS.events)
    if not events:
        return []
    return [create_event(i) for i in events]


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