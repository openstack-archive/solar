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

"""
Available controls:

*depends_on* implements relationship that will guarantee that depended action
on resource will be executed after parent, if parent will be executed. It means
that this control contributes only to ordering, and wont trigger any action
if dependent resource isnt changed.

    depends_on:
        - parent:run -> ok -> dependent:run

*react_on* - relationship which will guarantee that action on dependent
resource will be executed if parent action is going to be executed.
This control will trigger action even
if no changes noticed on dependent resource.

    react_on:
        - parent:update -> ok -> dependent:update
"""

from solar.dblayer.model import DBLayerNotFound
from solar.dblayer.solar_models import DBLayerSolarException
from solar.dblayer.solar_models import Resource


class Event(object):

    etype = None

    def __init__(self, parent, parent_action,
                 state='', child='', child_action=''):
        self.parent = parent
        self.parent_action = parent_action
        self.state = state
        self.child = child
        self.child_action = child_action

    @property
    def parent_node(self):
        return '{}.{}'.format(self.parent, self.parent_action)

    @property
    def child_node(self):
        return '{}.{}'.format(self.child, self.child_action)

    def to_dict(self):
        return {'etype': self.etype,
                'child': self.child,
                'parent': self.parent,
                'parent_action': self.parent_action,
                'child_action': self.child_action,
                'state': self.state}

    def __eq__(self, inst):
        if inst.__class__ != self.__class__:
            return False
        return all((
            self.parent_node == inst.parent_node,
            self.state == inst.state,
            self.child_node == inst.child_node))

    def __repr__(self):
        return '{}: {} -> {} -> {}'.format(
            self.etype, self.parent_node, self.state, self.child_node)

    def __hash__(self):
        return hash(repr(self))


class Dependency(Event):

    etype = 'depends_on'

    def insert(self, changed_resources, changes_graph):
        if (self.parent_node in changes_graph and
                self.child_node in changes_graph):
            changes_graph.add_edge(
                self.parent_node, self.child_node, state=self.state)

Dep = Dependency


class React(Event):

    etype = 'react_on'

    def insert(self, changed_resources, changes_graph):
        created = False
        if self.parent_node in changes_graph:
            if self.child_node not in changes_graph:
                try:
                    location_id = Resource.get(self.child).inputs[
                        'location_id']
                except (DBLayerNotFound, DBLayerSolarException):
                    location_id = None
                changes_graph.add_node(
                    self.child_node, status='PENDING',
                    target=location_id,
                    errmsg='', type='solar_resource',
                    args=[self.child, self.child_action])
                created = True
            changes_graph.add_edge(
                self.parent_node, self.child_node, state=self.state)
            changed_resources.append(self.child_node)
        return created


class StateChange(Event):

    etype = 'state_change'

    def insert(self, changed_resources, changes_graph):
        changed_resources.append(self.parent_node)
        try:
            location_id = Resource.get(self.parent).inputs['location_id']
        except (DBLayerNotFound, DBLayerSolarException):
            location_id = None
        changes_graph.add_node(
            self.parent_node, status='PENDING',
            target=location_id,
            errmsg='', type='solar_resource',
            args=[self.parent, self.parent_action])
