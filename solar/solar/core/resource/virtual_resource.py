# -*- coding: UTF-8 -*-
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
from StringIO import StringIO
import yaml

from jinja2 import Template, Environment, meta

from solar.core import provider
from solar.core import signals
from solar.core.resource import load as load_resource
from solar.core.resource import Resource
from solar.events.api import add_event
from solar.events.controls import React, Dep


def create(name, base_path, args=None, virtual_resource=None):
    args = args or {}
    if isinstance(base_path, provider.BaseProvider):
        base_path = base_path.directory

    if not os.path.exists(base_path):
        raise Exception(
            'Base resource does not exist: {0}'.format(base_path)
        )

    if is_virtual(base_path):
        template = _compile_file(name, base_path, args)
        yaml_template = yaml.load(StringIO(template))
        rs = create_virtual_resource(name, yaml_template)
    else:
        r = create_resource(name,
                            base_path,
                            args=args,
                            virtual_resource=virtual_resource)
        rs = [r]

    return rs


def create_resource(name, base_path, args=None, virtual_resource=None):
    args = args or {}
    if isinstance(base_path, provider.BaseProvider):
        base_path = base_path.directory

    # List args init with empty list. Elements will be added later
    args = {key: (value if not isinstance(value, list) else []) for key, value in args.items()}
    r = Resource(
        name, base_path, args=args, tags=[], virtual_resource=virtual_resource
    )
    return r


def create_virtual_resource(vr_name, template):
    template_resources = template['resources']
    template_events = template.get('events', [])
    resources_to_update = template.get('updates', {})

    created_resources = create_resources(template_resources)
    events = parse_events(template_events)
    for event in events:
        add_event(event)
    update_resources(resources_to_update)
    return created_resources


def _compile_file(name, path, kwargs):
    with open(path) as f:
        content = f.read()

    inputs = get_inputs(content)
    template = _get_template(name, content, kwargs, inputs)
    with open('/tmp/compiled', 'w') as c:
        c.write(template)
    return template


def get_inputs(content):
    env = Environment(trim_blocks=True, lstrip_blocks=True)
    jinja_globals = env.globals.keys()
    ast = env.parse(content)
    return meta.find_undeclared_variables(ast) - set(jinja_globals)


def _get_template(name, content, kwargs, inputs):
    missing = []
    for input in inputs:
        if input not in kwargs:
            missing.append(input)
    if missing:
        raise Exception('[{0}] Validation error. Missing data in input: {1}'.format(name, missing))
    template = Template(content, trim_blocks=True, lstrip_blocks=True)
    template = template.render(str=str, zip=zip, **kwargs)
    return template


def is_virtual(path):
    return os.path.isfile(path)


def create_resources(resources):
    created_resources = []
    cwd = os.getcwd()
    for r in resources:
        resource_name = r['id']
        args = r['values']
        from_path = r.get('from', None)
        base_path = os.path.join(cwd, from_path)
        new_resources = create(resource_name, base_path)
        created_resources += new_resources
        if not is_virtual(base_path):
            update_inputs(resource_name, args)
    return created_resources


def update_resources(resources):
    for r in resources:
        resource_name = r['id']
        args = r['values']
        update_inputs(resource_name, args)


def update_inputs(child, args):
    child = load_resource(child)
    connections, assignments = parse_inputs(args)
    for c in connections:
        mapping = {}
        parent = load_resource(c['parent'])
        events = c['events']
        mapping[c['parent_input']] = c['child_input']
        signals.connect(parent, child, mapping, events)

    child.update(assignments)


def parse_events(events):
    parsed_events = []
    for event in events:
        event_type = event['type']
        parent, parent_action = event['parent_action'].split('.')
        child, child_action = event['depend_action'].split('.')
        state = event['state']
        if event_type == Dep.etype:
            event = Dep(parent, parent_action, state, child, child_action)
        elif event_type == React.etype:
            event = React(parent, parent_action, state, child, child_action)
        else:
            raise Exception('Invalid event type: {0}'.format(event_type))
        parsed_events.append(event)
    return parsed_events


def parse_inputs(args):
    connections = []
    assignments = {}
    for r_input, arg in args.items():
        if isinstance(arg, list):
            c, a = parse_list_input(r_input, arg)
            connections.extend(c)
            assignments.update(a)
        else:
            if isinstance(arg, basestring) and '::' in arg:
                c = parse_connection(r_input, arg)
                connections.append(c)
            else:
                assignments[r_input] = arg
    return connections, assignments


def parse_list_input(r_input, args):
    connections = []
    assignments = {}
    for arg in args:
        if isinstance(arg, basestring) and '::' in arg:
            c = parse_connection(r_input, arg)
            connections.append(c)
        else:
            # Not supported yet
            pass
    return connections, assignments


def parse_connection(child_input, element):
    parent, parent_input = element.split('::', 1)
    try:
        parent_input, events = parent_input.split('::')
        if events == 'NO_EVENTS':
            events = False
    except ValueError:
        events = None
    return {'child_input': child_input,
            'parent' : parent,
            'parent_input': parent_input,
            'events' : events
            }
