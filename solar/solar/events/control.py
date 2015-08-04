"""
Available controls:

*depends_on* implements relationship that will guarantee that depended action
on resource will be executed after parent, if parent will be executed. It means
that this control contributes only to ordering, and wont trigger any action
if dependent resource isnt changed.

    depends_on:
        - parent:run -> ok -> dependent:run

*react_on* - relationship which will guarantee that action on dependent resource
will be executed if parent action is going to be executed. This control will
trigger action even if no changes noticed on dependent resource.

    react_on:
        - parent:update -> ok -> dependent:update
"""

import re

from solar.core.log import log



class Event(object):

    etype = None

    def __init__(self, parent_node, parent_action,
                 state, depend_node, depend_action):
        self.parent_node = parent_node
        self.parent_action = parent_action
        self.state = state
        self.depend_node = depend_node
        self.depend_action = depend_action

    @property
    def parent(self):
        return '{}:{}'.format(self.parent_node, self.parent_action)

    @property
    def dependent(self):
        return '{}:{}'.format(self.depend_node, self.depend_action)

    def to_dict(self):
        rst = {'etype': self.etype}
        rst.update(self.__dict__)
        return rst

    def __eq__(self, inst):
        if inst.__class__ != self.__class__:
            return False
        return all((
            self.parent == inst.parent,
            self.state == inst.state,
            self.dependent == inst.dependent))

    def __repr__(self):
        return '{}: {} -> {} -> {}'.format(
            self.etype, self.parent, self.state, self.dependent)


class Dependency(Event):

    etype = 'depends_on'

    def add(self, changed_resources, changes_graph):
        if self.parent in changes_graph:
            changes_graph.add_edge(
                self.parent, self.dependent, state=self.state)


class React(Event):

    etype = 'react_on'

    def add(self, changed_resources, changes_graph):
        changes_graph.add_edge(self.parent, self.dependent, state=self.state)
        changed_resources.append(self.dep_node)


def build_edges(changed_resources, changes_graph, events):
    """
    :param changed_resources: list of resource names that were changed
    :param changes_graph: nx.DiGraph object with actions to be executed
    :param events: {node: [(event_type, event_expr)]}
    """
    stack = changed_resources[:]
    while stack:
        node = stack.pop()
        events_objects = []

        for event_type, node in events[node].iteritems():
            log.debug('Events %s for resource %s', events[node], node)
            if event_type == 'react_on':
                create_event(e).add(stack, changes_graph)
            elif event_type == 'depends_on':
                create_event(e).add(stack, changes_graph)

    return changes_graph
