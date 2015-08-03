# -*- coding: UTF-8 -*-
import os
from StringIO import StringIO

import yaml

from jinja2 import Template, Environment, meta

from solar import utils
from solar.core import validation
from solar.core.resource import load_all, Resource
from solar.core import provider
from solar.core import signals


def create_resource(name, base_path, args, virtual_resource=None):
    if isinstance(base_path, provider.BaseProvider):
        base_path = base_path.directory

    base_meta_file = os.path.join(base_path, 'meta.yaml')
    actions_path = os.path.join(base_path, 'actions')

    metadata = utils.yaml_load(base_meta_file)
    metadata['id'] = name
    metadata['version'] = '1.0.0'
    metadata['base_path'] = os.path.abspath(base_path)

    prepare_meta(metadata)

    if os.path.exists(actions_path):
        for f in os.listdir(actions_path):
            metadata['actions'][os.path.splitext(f)[0]] = f

    tags = metadata.get('tags', [])

    resource = Resource(name, metadata, args, tags, virtual_resource)
    return resource


def create_virtual_resource(vr_name, template):
    resources = template['resources']
    connections = []
    created_resources = []

    cwd = os.getcwd()
    for resource in resources:
        name = resource['id']
        base_path = os.path.join(cwd, resource['from'])
        args = resource['values']
        new_resources = create(name, base_path, args, vr_name)
        created_resources += new_resources

        if not is_virtual(base_path):
            for key, arg in args.items():
                if isinstance(arg, basestring) and '::' in arg:
                    emitter, src = arg.split('::')
                    connections.append((emitter, name, {src: key}))

        db = load_all()
        for emitter, reciver, mapping in connections:
            emitter = db[emitter]
            reciver = db[reciver]
            signals.connect(emitter, reciver, mapping)

    return created_resources


def create(name, base_path, kwargs, virtual_resource=None):
    if isinstance(base_path, provider.BaseProvider):
        base_path = base_path.directory

    if not os.path.exists(base_path):
        raise Exception(
            'Base resource does not exist: {0}'.format(base_path)
        )

    if is_virtual(base_path):
        template = _compile_file(name, base_path, kwargs)
        yaml_template = yaml.load(StringIO(template))
        resources = create_virtual_resource(name, yaml_template)
    else:
        resource = create_resource(name, base_path, kwargs, virtual_resource)
        resources = [resource]

    return resources


def prepare_meta(meta):
    actions_path = os.path.join(meta['base_path'], 'actions')
    meta['actions_path'] = actions_path
    meta['base_name'] = os.path.split(meta['base_path'])[-1]

    meta['actions'] = {}
    if os.path.exists(meta['actions_path']):
        for f in os.listdir(meta['actions_path']):
            meta['actions'][os.path.splitext(f)[0]] = f


def validate_resources():
    db = load_all()
    all_errors = []
    for r in db.values():
        if not isinstance(r, Resource):
            continue

        errors = validation.validate_resource(r)
        if errors:
            all_errors.append((r, errors))
    return all_errors


def find_inputs_without_source():
    """Find resources and inputs values of which are hardcoded.

    :return: [(resource_name, input_name)]
    """
    resources = load_all()

    ret = set([(r.name, input_name) for r in resources.values()
               for input_name in r.args])

    clients = signals.Connections.read_clients()

    for dest_dict in clients.values():
        for destinations in dest_dict.values():
            for receiver_name, receiver_input in destinations:
                try:
                    ret.remove((receiver_name, receiver_input))
                except KeyError:
                    continue

    return list(ret)


def find_missing_connections():
    """Find resources whose input values are duplicated

    and they are not connected between each other (i.e. the values
    are hardcoded, not coming from connection).

    NOTE: this we could have 2 inputs of the same value living in 2 "circles".
    This is not covered, we find only inputs whose value is hardcoded.

    :return: [(resource_name1, input_name1, resource_name2, input_name2)]
    """
    ret = set()

    resources = load_all()

    inputs_without_source = find_inputs_without_source()

    for resource1, input1 in inputs_without_source:
        r1 = resources[resource1]
        v1 = r1.args[input1]

        for resource2, input2 in inputs_without_source:
            r2 = resources[resource2]
            v2 = r2.args[input2]

            if v1 == v2 and resource1 != resource2 and \
                    (resource2, input2, resource1, input1) not in ret:
                ret.add((resource1, input1, resource2, input2))

    return list(ret)


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

