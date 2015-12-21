# -*- coding: utf-8 -*-
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

from collections import defaultdict
import os
from StringIO import StringIO

from jinja2 import Environment
from jinja2 import meta
import yaml

from solar.core.log import log
from solar.core import provider
from solar.core.resource.repository import Repository
from solar.core.resource import load as load_resource
from solar.core.resource import load_by_tags
from solar.core.resource import Resource
from solar.events.api import add_event
from solar.events.controls import Dep
from solar.events.controls import React


# Custom environment with custom blocks, to make yaml parsers happy
VR_ENV = Environment(block_start_string="#%",
                     block_end_string="%#",
                     variable_start_string="#{",
                     variable_end_string="}#",
                     trim_blocks=True,
                     lstrip_blocks=True)


def create(name, spec, args=None, tags=None, virtual_resource=None):
    args = args or {}
    if isinstance(spec, provider.BaseProvider):
        spec = spec.directory

    repo, parsed_spec = Repository.parse(spec)

    if repo.is_virtual(spec):
        path = repo.get_virtual_path(spec)
        template = _compile_file(name, path, args)
        yaml_template = yaml.load(StringIO(template))
        rs = create_virtual_resource(name, yaml_template, tags)
    else:
        r = create_resource(name,
                            spec,
                            args=args,
                            tags=tags,
                            virtual_resource=virtual_resource)
        rs = [r]

    return rs


def create_resource(name, spec, args=None, tags=None,
                    virtual_resource=None):
    args = args or {}
    if isinstance(spec, provider.BaseProvider):
        spec = spec.directory

    # filter connections from lists and dicts
    # will be added later
    def _filter(value):
        if isinstance(value, list):
            return filter(lambda res: not is_connection(res), value)
        if isinstance(value, dict):
            return {key: None if is_connection(value) else value
                    for key, value in value.iteritems()}
        else:
            return value

    args = {key: _filter(value) for key, value in args.items()}
    r = Resource(name, spec, args=args,
                 tags=tags, virtual_resource=virtual_resource)
    return r


def create_virtual_resource(vr_name, template, tags=None):
    template_resources = template.get('resources', [])
    template_events = template.get('events', [])
    resources_to_update = template.get('updates', [])

    created_resources = create_resources(template_resources, tags=tags)
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
    jinja_globals = VR_ENV.globals.keys()
    ast = VR_ENV.parse(content)
    return meta.find_undeclared_variables(ast) - set(jinja_globals)


def _get_template(name, content, kwargs, inputs):
    missing = []
    for input in inputs:
        if input not in kwargs:
            missing.append(input)
    if missing:
        raise Exception(
            '[{0}] Validation error. Missing data in input: {1}'.format(name, missing))  # NOQA
    template = VR_ENV.from_string(content)
    template = template.render(str=str, zip=zip, **kwargs)
    return template


def create_resources(resources, tags=None):
    created_resources = []
    for r in resources:
        resource_name = r['id']
        args = r.get('values', {})
        node = r.get('location', None)
        values_from = r.get('values_from')
        spec = r.get('from', None)
        tags = r.get('tags', [])
        new_resources = create(resource_name, spec, args=args, tags=tags)
        created_resources += new_resources
        repo, parsed_spec = Repository.parse(spec)
        if not repo.is_virtual(parsed_spec):
            if node:
                node = load_resource(node)
                r = new_resources[0]
                node.connect(r, mapping={})
                r.add_tags('location={}'.format(node.name))

            update_inputs(resource_name, args)

            if values_from:
                from_resource = load_resource(values_from)
                from_resource.connect_with_events(r, use_defaults=False)

    return created_resources


def extend_resources(template_resources):
    resources = []
    for r in template_resources:
        if r.get('id'):
            resources.append(r)
        if r.get('with_tags'):
            tags = r.get('with_tags')
            filtered = load_by_tags(tags)
            for f in filtered:
                r = {'id': f.name,
                     'values': r['values']}
                resources.append(r)
                log.debug('Resource {} for tags {} found'.format(r, tags))
            if not filtered:
                log.debug('Warrning: no resources with tags: {}'.format(tags))
    return resources


def update_resources(template_resources):
    resources = extend_resources(template_resources)
    for r in resources:
        resource_name = r['id']
        args = r['values']
        update_inputs(resource_name, args)


def update_inputs(child, args):
    child = load_resource(child)
    connections, assignments = parse_inputs(args)
    parents = defaultdict(lambda: defaultdict(dict))
    for c in connections:
        mapping = {c['parent_input']: c['child_input']}
        parents[c['parent']]['mapping'].update(mapping)
        if parents[c['parent']].get('events', None) is None:
            parents[c['parent']]['events'] = c['events']

    for parent, data in parents.iteritems():
        parent = load_resource(parent)
        use_defaults = not data['events'] is False
        mapping = data['mapping']
        parent.connect_with_events(
            child, mapping, {}, use_defaults=use_defaults)

    child.update(assignments)


def extend_events(template_events):
    events = []
    for e in template_events:
        if e.get('parent_action', None):
            events.append(e)
        elif e.get('parent', None):
            parent = e.get('parent')
            tags = parent.get('with_tags')
            resources = load_by_tags(tags)
            for r in resources:
                parent_action = '{}.{}'.format(r.name, parent['action'])
                event = {'type': e['type'],
                         'state': e['state'],
                         'depend_action': e['depend_action'],
                         'parent_action': parent_action
                         }
                events.append(event)
    return events


def parse_events(template_events):
    parsed_events = []
    events = extend_events(template_events)
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
        elif isinstance(arg, dict):
            c, a = parse_dict_input(r_input, arg)
            connections.extend(c)
            assignments.update(a)
        else:
            if is_connection(arg):
                c = parse_connection(r_input, arg)
                connections.append(c)
            else:
                assignments[r_input] = arg
    return connections, assignments


def parse_list_input(r_input, args):
    connections = []
    assignments = {}
    for arg in args:
        if isinstance(arg, dict):
            n_connections, n_assign = parse_dict_input(
                r_input, arg)
            connections.extend(n_connections)
            if n_assign:
                add_assignment(assignments, r_input, n_assign)
        elif is_connection(arg):
            c = parse_connection(r_input, arg)
            connections.append(c)
        else:
            add_assignment(assignments, r_input, arg)
    return connections, assignments


def parse_dict_input(r_input, args):
    connections = []
    assignments = {}
    for key, value in args.iteritems():
        if is_connection(value):
            dict_input = '{}:{}'.format(r_input, key)
            c = parse_connection(dict_input, value)
            connections.append(c)
        else:
            try:
                assignments[r_input][key] = value
            except KeyError:
                assignments[r_input] = {key: value}
    return connections, assignments


def add_assignment(assignments, r_input, arg):
    try:
        assignments[r_input].append(arg)
    except KeyError:
        assignments[r_input] = [arg]


def is_connection(arg):
    if isinstance(arg, basestring) and '::' in arg:
        return True
    return False


def parse_connection(child_input, element):
    parent, parent_input = element.split('::', 1)
    try:
        parent_input, events = parent_input.split('::')
        if events == 'NO_EVENTS':
            events = False
    except ValueError:
        events = None
    return {'child_input': child_input,
            'parent': parent,
            'parent_input': parent_input,
            'events': events
            }
