# -*- coding: UTF-8 -*-
import os
from StringIO import StringIO

import yaml

from jinja2 import Template, Environment, meta

from solar import utils
from solar.core import validation
from solar.core import resource as resource_module
from solar.core import signals


def create_resource(name, base_path, args, virtual_resource=None):
    from solar.core import resource_provider

    if isinstance(base_path, resource_provider.BaseProvider):
        base_path = base_path.directory

    base_meta_file = os.path.join(base_path, 'meta.yaml')
    actions_path = os.path.join(base_path, 'actions')

    metadata = utils.yaml_load(base_meta_file)
    metadata['id'] = name
    metadata['version'] = '1.0.0'
    metadata['actions'] = {}
    metadata['actions_path'] = actions_path
    metadata['base_path'] = os.path.abspath(base_path)

    if os.path.exists(actions_path):
        for f in os.listdir(actions_path):
            metadata['actions'][os.path.splitext(f)[0]] = f

    tags = metadata.get('tags', [])

    resource = resource_module.Resource(name, metadata, args, tags, virtual_resource)
    return resource

def create_virtual_resource(vr_name, template):
    resources = template['resources']
    connections = []
    created_resources = []
    for resource in resources:
        name = resource['id']
        base_path = resource['from']
        args = resource['values']
        new_resources = create(name, base_path, args, vr_name)
        created_resources += new_resources

        if not is_virtual(base_path):
            for key, arg in args.items():
                if isinstance(arg, basestring) and '::' in arg:
                    emitter, src = arg.split('::')
                    connections.append((emitter, name, {src: key}))

        db = resource_module.load_all()
        for emitter, reciver, mapping in connections:
            emitter = db[emitter]
            reciver = db[reciver]
            signals.connect(emitter, reciver, mapping)

        for r in db.values():
            if not isinstance(r, resource_module.Resource):
                continue

            print 'Validating {}'.format(r.name)
            errors = validation.validate_resource(r)
            if errors:
                print 'ERROR: %s: %s' % (r.name, errors)
                #import sys;sys.exit()
    return created_resources

def create(name, path, kwargs, virtual_resource=None):
    if not os.path.exists(path):
        raise Exception('Base resource does not exist: {0}'.format(path))

    if is_virtual(path):
        template = _compile_file(name, path, kwargs)
        yaml_template = yaml.load(StringIO(template))
        resources = create_virtual_resource(name, yaml_template)
    else:
        resource = create_resource(name, path, kwargs, virtual_resource)
        resources = [resource]

    return resources

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
