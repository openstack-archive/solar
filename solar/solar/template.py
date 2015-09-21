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

import os

from solar.core.resource import virtual_resource as vr
from solar.core import signals
from solar.events.api import add_event
from solar.events import controls


class BaseTemplate(object):
    """Base object for the template language."""

    @staticmethod
    def args_fmt(args, kwargs):
        def fmt(v, kwargs):
            if isinstance(v, basestring):
                return v.format(**kwargs)
            return v

        return {
            fmt(k, kwargs): fmt(v, kwargs) for k, v in args.items()
        }

    @staticmethod
    def action_state_parse(action_state):
        action, state = action_state.split('/')

        return {
            'action': action,
            'state': state,
        }


class ResourceTemplate(BaseTemplate):
    """Template for single resource object."""

    def __init__(self, resource):
        """Initialize with solar.resource.Resource instance."""

        self.resource = resource

    def add_dep(self, action_state, resource, action):
        """Add single orch Dep from self to resource.

        resource = resources.take(0)
        resource.add_dep('run/success', some_resource, 'run')
        """

        action_state = self.action_state_parse(action_state)

        add_event(
            controls.Dep(
                self.resource.name,
                action_state['action'],
                action_state['state'],
                resource.resource.name,
                action
            )
        )

    def add_react(self, action_state, resource, action):
        """Add single orch React from self to resource.

        resource = resources.take(0)
        resource.add_react('run/success', some_resource, 'run')
        """

        action_state = self.action_state_parse(action_state)

        add_event(
            controls.React(
                self.resource.name,
                action_state['action'],
                action_state['state'],
                resource.resource.name,
                action
            )
        )

    def connect_list(self, resources, mapping=None):
        """Connect this resource to a ResourceListTemplate object.

        mapping - optional connect mapping. This mapping can have the
          "{receiver_num}" string which enumerates each resrouce in resources
          list.
        """
        mapping = mapping or {}

        for receiver_num, resource in enumerate(resources.resources):
            kwargs = {
                'receiver_num': receiver_num,
            }

            mapping_fmt = self.args_fmt(mapping, kwargs)

            signals.connect(self.resource, resource, mapping_fmt)


class ResourceListTemplate(BaseTemplate):
    """Template for object representing multiple resources."""

    def __init__(self, resources):
        """Initialize with list of solar.resource.Resource instances."""

        self.resources = resources

    @classmethod
    def create(cls,
               count,
               resource_path,
               name='{resource_path_name}-{num}',
               args=None):
        """Create a number of resources of the same type, with optional args.

        name -- optional resource name
        args -- an optional dict with create arguments. You can use
          "{num}" -- index of resource in the list
          "{resource_path_name}" -- name of resource from the `resource_path`
            argument
        """

        args = args or {}

        created_resources = []

        resource_path_name = os.path.split(resource_path)[-1]

        for num in range(count):
            kwargs = {
                'num': num,
                'resource_path_name': resource_path_name,
            }
            kwargs['name'] = name.format(**kwargs)

            args_fmt = cls.args_fmt(args, kwargs)

            r = vr.create(kwargs['name'],
                          resource_path,
                          args_fmt)[0]

            created_resources.append(r)

        return ResourceListTemplate(created_resources)

    def add_dep(self, action_state, resource, action):
        """Calls add_dep for every resource in self."""

        for r in self.resources:
            ResourceTemplate(r).add_dep(
                action_state,
                resource,
                action
            )

    def add_deps(self, action_state, resources, action):
        """Same as add_dep but adds dep for resources.

        resources -- an instance of ResourceListTemplate class
        """

        for r, dep_r in zip(self.resources, resources.resources):
            ResourceTemplate(r).add_dep(
                action_state,
                ResourceTemplate(dep_r),
                action
            )

    def add_react(self, action_state, resource, action):
        """Calls add_react for every resource in self."""

        for r in self.resources:
            ResourceTemplate(r).add_react(
                action_state,
                resource,
                action
            )

    def add_reacts(self, action_state, resources, action):
        """Same as add_react but adds react for resources.

        resources -- an instance of ResourceListTemplate class
        """

        for r in resources.resources:
            self.add_react(action_state, ResourceTemplate(r), action)

    def filter(self, func):
        """Return ResourceListeTemplate instance with resources filtered by func.

        func -- predictate function that takes (idx, resource) as parameter
          (idx is the index of resource in self.resources list)
        """

        resources = filter(func, enumerate(self.resources))

        return ResourceListTemplate(resources)

    def connect_list(self, resources, mapping=None, events=None):
        """Connect self.resources to given resources in a 1-1 fashion.

        First resource in self.resources is connected to first resource in
        resources, second to second, etc.

        mapping -- optional mapping
          "{num}" -- substitutes for resource's index in args
        """
        mapping = mapping or {}

        for num, er in enumerate(zip(self.resources, resources.resources)):
            emitter, receiver = er

            kwargs = {
                'num': num,
            }

            mapping_fmt = self.args_fmt(mapping, kwargs)

            signals.connect(
                emitter, receiver, mapping=mapping_fmt, events=events
            )

    def connect_list_to_each(self, resources, mapping=None, events=None):
        """Connect each resource in self.resources to each resource in resources.

        mapping -- optional mapping
          "{emitter_num}" -- substitutes for emitter's index in mapping (from
            self.resources)
          "{receiver_num}" -- substitutes for receiver's index in mapping (from
            resources argument)
        """
        mapping = mapping or {}

        for emitter_num, emitter in enumerate(self.resources):
            for receiver_num, receiver in enumerate(resources.resources):
                kwargs = {
                    'emitter_num': emitter_num,
                    'receiver_num': receiver_num,
                }

                mapping_fmt = self.args_fmt(mapping, kwargs)

                signals.connect(
                    emitter,
                    receiver,
                    mapping=mapping_fmt,
                    events=events
                )

    def on_each(self, resource_path, args=None):
        """Create resource form resource_path on each resource in self.resources.
        """
        args = args or {}

        created_resources = ResourceListTemplate.create(
            len(self.resources),
            resource_path,
            args=args
        )

        for i, resource in enumerate(self.resources):
            signals.connect(resource, created_resources.resources[i])

        return created_resources

    def take(self, i):
        """Return ResourceTemplate from self.resources[i]."""

        return ResourceTemplate(self.resources[i])

    def tail(self):
        """Return ResourceListTemplate form self.resources[1:]."""

        return ResourceListTemplate(self.resources[1:])


def nodes_from(template_path):
    """Return ResourceListTemplate for nodes read from template_path."""

    nodes = vr.create('nodes', template_path, {})
    return ResourceListTemplate(nodes)
