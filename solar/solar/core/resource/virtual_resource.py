import os
from StringIO import StringIO
import yaml

from jinja2 import Template, Environment, meta

from solar.core import provider
from solar.core.resource.resource import Resource


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
        raise Exception('Virtual resource not implemented')
        #resources = create_virtual_resource(name, yaml_template)
    else:
        resource = create_resource(name, base_path, kwargs, virtual_resource)
        resources = [resource]

    return resources


def create_resource(name, base_path, args, virtual_resource=None):
    if isinstance(base_path, provider.BaseProvider):
        base_path = base_path.directory

    resource = Resource(
        name, base_path, args, tags=[], virtual_resource=virtual_resource
    )
    return resource


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
