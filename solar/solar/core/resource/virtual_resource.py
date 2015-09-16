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
from solar.core import resource
from solar.core import signals


def create(name, base_path, args={}, virtual_resource=None):
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


def create_resource(name, base_path, args={}, virtual_resource=None):
    if isinstance(base_path, provider.BaseProvider):
        base_path = base_path.directory

    r = resource.Resource(
        name, base_path, args=args, tags=[], virtual_resource=virtual_resource
    )
    return r


def create_virtual_resource(vr_name, template):
    resources = template['resources']
    connections = []
    created_resources = []

    cwd = os.getcwd()
    for r in resources:
        name = r['id']
        base_path = os.path.join(cwd, r['from'])
        args = r['values']
        new_resources = create(name, base_path, args, vr_name)
        created_resources += new_resources

        if not is_virtual(base_path):
            for key, arg in args.items():
                if isinstance(arg, basestring) and '::' in arg:
                    emitter, src = arg.split('::')
                    connections.append((emitter, name, {src: key}))

        for emitter, reciver, mapping in connections:
            emitter = r.load(emitter)
            reciver = r.load(reciver)
            signals.connect(emitter, reciver, mapping)

    return created_resources


def _compile_file(name, path, kwargs):
    with open(path) as f:
        content = f.read()

    inputs = get_inputs(content)
    template = _get_template(name, content, kwargs, inputs)
    return template


def get_inputs(content):
    env = Environment()
    ast = env.parse(content)
    return meta.find_undeclared_variables(ast)


def _get_template(name, content, kwargs, inputs):
    missing = []
    for input in inputs:
        if input not in kwargs:
            missing.append(input)
    if missing:
        raise Exception('[{0}] Validation error. Missing data in input: {1}'.format(name, missing))
    template = Template(content)
    template = template.render(str=str, zip=zip, **kwargs)
    return template


def is_virtual(path):
    return os.path.isfile(path)
