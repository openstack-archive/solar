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
from collections import OrderedDict
from StringIO import StringIO

from jinja2 import Environment
from jinja2 import meta


import os
import re
import yaml

from solar.core.log import log
from solar.core import provider
from solar.core.resource import load as load_resource
from solar.core.resource import load_by_tags
from solar.core.resource.repository import Repository
from solar.core.resource import Resource
from solar.events.api import add_event
from solar.events.controls import Dep
from solar.events.controls import React


# Custom environment with custom blocks, to make yaml parsers happy
# globals extendend at the very end
VR_ENV = Environment(block_start_string="#%",
                     block_end_string="%#",
                     variable_start_string="#{",
                     variable_end_string="}#",
                     trim_blocks=True,
                     lstrip_blocks=True)


class CreatedResources(object):

    def __init__(self, resources):
        if isinstance(resources, (list, tuple)):
            c = OrderedDict((r.name, r) for r in resources)
        else:
            c = resources
        self.data = c

    def __getitem__(self, key):
        if isinstance(key, int):
            key = self.data.keys()[key]
        return self.data[key]

    def __iter__(self):
        return self.data.itervalues()

    def __len__(self):
        return self.data.__len__()

    def like(self, regex):
        keys = self.data.keys()
        matched_keys = filter(lambda key: re.match(regex, key), keys)
        return CreatedResources(
            OrderedDict((rname, self[rname]) for rname in matched_keys))


def create(name, spec, inputs=None, tags=None):
    inputs = inputs or {}
    if isinstance(spec, provider.BaseProvider):
        spec = spec.directory

    # fullpath
    # TODO: (jnowak) find a better way to code this part
    if spec.startswith('/'):
        if os.path.isfile(spec):
            template = _compile_file(name, spec, inputs)
            yaml_template = yaml.load(StringIO(template))
            rs = apply_composer_file(spec, name, yaml_template, tags)
        else:
            r = create_resource(name, spec, inputs=inputs, tags=tags,)
            rs = [r]
        return rs

    repo, parsed_spec = Repository.parse(spec)

    if repo.is_composer_file(spec):
        path = repo.get_composer_file_path(spec)
        template = _compile_file(name, path, inputs)
        yaml_template = yaml.load(StringIO(template))
        rs = apply_composer_file(path, name, yaml_template, tags)
    else:
        r = create_resource(name, spec, inputs=inputs, tags=tags)
        rs = [r]

    return CreatedResources(rs)


def create_resource(name, spec, inputs=None, tags=None):
    inputs = inputs or {}
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

    inputs = {key: _filter(value) for key, value in inputs.items()}
    r = Resource(name, spec, args=inputs, tags=tags)
    return r


def apply_composer_file(base_path, vr_name, template, tags=None):
    template_resources = template.get('resources', [])
    template_events = template.get('events', [])
    resources_to_update = template.get('updates', [])

    created_resources = create_resources(
        base_path,
        template_resources,
        tags=tags
    )
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


def _fix_content(content):
    start = VR_ENV.variable_start_string
    end = VR_ENV.variable_end_string
    return re.sub(r'%s([^}]+)%s' % (start, end),
                  r'%sdump_back(\1)%s' % (start, end),
                  content)


def _get_template(name, content, kwargs, inputs):
    missing = []
    for input in inputs:
        if input not in kwargs:
            missing.append(input)
    if missing:
        raise Exception(
            '[{0}] Validation error. Missing data in input: {1}'.format(name, missing))  # NOQA
    content = _fix_content(content)
    template = VR_ENV.from_string(content)
    template = template.render(str=str, zip=zip, **kwargs)
    return template


def create_resources(base_path, resources, tags=None):
    add_tags = tags
    created_resources = []
    for r in resources:
        resource_name = r['id']
        inputs = r.get('input', {})
        node = r.get('location', None)
        values_from = r.get('values_from')
        spec = r.get('from', None)
        tags = r.get('tags', [])
        if add_tags:
            tags.extend(add_tags)
        is_composer_file = False
        if spec.startswith('./') or spec.endswith('.yaml'):
            spec = os.path.join(base_path, '..', spec)
            spec = os.path.abspath(os.path.normpath(spec))
            is_composer_file = True

        new_resources = create(resource_name, spec, inputs=inputs, tags=tags)
        created_resources += new_resources

        if not spec.startswith('/'):
            repo, parsed_spec = Repository.parse(spec)
            is_composer_file = repo.is_composer_file(spec)
        if not is_composer_file:
            if node:
                node = load_resource(node)
                r = new_resources[0]
                node.connect(r, mapping={})
                r.add_tags('location={}'.format(node.name))

            update_inputs(resource_name, inputs)

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
                     'input': r['input']}
                resources.append(r)
                log.debug('Resource {} for tags {} found'.format(r, tags))
            if not filtered:
                log.debug('Warrning: no resources with tags: {}'.format(tags))
    return resources


def update_resources(template_resources):
    resources = extend_resources(template_resources)
    for r in resources:
        resource_name = r['id']
        inputs = r['input']
        update_inputs(resource_name, inputs)


def update_inputs(child, inputs):
    child = load_resource(child)
    connections, assignments, computable = parse_inputs(inputs)
    parents = defaultdict(lambda: defaultdict(dict))
    for c in connections:
        if not parents[c['parent']]['mapping'].get(c['parent_input']):
           parents[c['parent']]['mapping'][c['parent_input']] = []
        parents[c['parent']]['mapping'][c['parent_input']].append(c['child_input'])
        if parents[c['parent']].get('events', None) is None:
            parents[c['parent']]['events'] = c['events']

    for parent, data in parents.iteritems():
        parent = load_resource(parent)
        use_defaults = not data['events'] is False
        mapping = data['mapping']
        parent.connect_with_events(
            child, mapping, {}, use_defaults=use_defaults)

    child.update(assignments)

    for comp in computable:
        child.input_computable_change(**comp)


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
                         'child_action': e['child_action'],
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
        child, child_action = event['child_action'].split('.')
        state = event['state']
        if event_type == Dep.etype:
            event = Dep(parent, parent_action, state, child, child_action)
        elif event_type == React.etype:
            event = React(parent, parent_action, state, child, child_action)
        else:
            raise Exception('Invalid event type: {0}'.format(event_type))
        parsed_events.append(event)
    return parsed_events


def parse_inputs(inputs):
    connections = []
    assignments = {}
    computable = []
    for r_input, arg in inputs.items():
        if isinstance(arg, list):
            c, a = parse_list_input(r_input, arg)
            connections.extend(c)
            assignments.update(a)
        elif isinstance(arg, dict):
            if 'computable' in arg:
                comp, conn = parse_computable_input(r_input, arg)
                computable.append(comp)
                connections.extend(conn)
            else:
                c, a = parse_dict_input(r_input, arg)
                connections.extend(c)
                assignments.update(a)
        else:
            if is_connection(arg):
                c = parse_connection(r_input, arg)
                connections.append(c)
            else:
                assignments[r_input] = arg
    return connections, assignments, computable


def parse_list_input(r_input, args):
    connections = []
    assignments = []
    for arg in args:
        if isinstance(arg, dict):
            n_connections, n_assign = parse_dict_input(
                r_input, arg)
            connections.extend(n_connections)
            if n_assign:
                assignments.append(n_assign[r_input])
        elif is_connection(arg):
            c = parse_connection(r_input, arg)
            connections.append(c)
        else:
            assignments.append(arg)
    if assignments:
        assignments = {r_input: assignments}
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


def parse_computable_input(r_input, arg):
    computable = {'name': r_input}
    connections = []
    data = arg['computable']
    func = data.get('func', None)
    d_type = data.get('type', None)
    lang = data.get('lang', None)
    if func:
        computable['func'] = func
    if d_type:
        computable['type'] = d_type
    if lang:
        computable['lang'] = lang
    for c in data.get('connections', []):
        c = parse_connection(r_input, c)
        connections.append(c)
    return computable, connections


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


# TODO: this is rather temporary solution
# we need to find better way of solving this prolbem
# please look at lp #1539174
def dump_back_to_file(data):
    val = yaml.safe_dump(data)
    if val.endswith('\n...\n'):
        # yaml dumps in that way, when we operate on single value
        val = val[:-5]
    if val.endswith('\n'):
        # yaml dumps in that way, when we operate on single value
        val = val[:-1]
    return val

VR_ENV.globals['dump_back'] = dump_back_to_file
