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


EVENT = re.compile(r'\s+->\s+')


class Event(object):

    def __init__(self, event):
        self.parent, self.dependent, self.state = EVENT.split(event)
        self.parent_node, self.parent_action = self.parent.split(':')
        self.dep_node, self.dep_action = self.dependent.split(':')

    def __repr__(self):
        return '{}({} -> {} -> {})'.format(
            self.__class__.__name__,
            self.parent, self.dependent, self.state)


class Dependency(Event):

    def add(self, changed_resources, changes_graph):
        if self.parent in changes_graph:
            changes_graph.add_edge(
                self.parent, self.dependent, state=self.state)


class React(Event):

    def add(self, changed_resources, changes_graph):
        changes_graph.add_edge(self.parent, self.dependent, state=self.state)
        changed_resources.append(self.dep_node)


def build_edges(changed_resources, changes_graph, events):
    """
    :param changed_resources: list of resource names that were changed
    :param changes_graph: nx.DiGraph object with actions to be executed
    :param events:
    """
    stack = changed_resources[:]
    while stack:
        node = stack.pop()
        events_objects = []

        if node in events:
            log.debug('Events %s for resource %s', events[node], node)

            for e in events[node].get('react_on', ()):
                React(e).add(stack, changes_graph)
            for e in events[node].get('depends_on', ()):
                Dependency(e).add(stack, changes_graph)

    return changes_graph