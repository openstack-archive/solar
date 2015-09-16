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

from copy import deepcopy
from multipledispatch import dispatch
import os

from solar import utils
from solar.core import validation
from solar.interfaces import orm


def read_meta(base_path):
    base_meta_file = os.path.join(base_path, 'meta.yaml')

    metadata = utils.yaml_load(base_meta_file)
    metadata['version'] = '1.0.0'
    metadata['base_path'] = os.path.abspath(base_path)
    actions_path = os.path.join(metadata['base_path'], 'actions')
    metadata['actions_path'] = actions_path
    metadata['base_name'] = os.path.split(metadata['base_path'])[-1]

    return metadata


class Resource(object):
    _metadata = {}

    # Create
    @dispatch(str, str)
    def __init__(self, name, base_path, args=None, tags=None, virtual_resource=None):
        args = args or {}
        self.name = name
        if base_path:
            metadata = read_meta(base_path)
        else:
            metadata = deepcopy(self._metadata)

        self.tags = tags or []
        self.virtual_resource = virtual_resource

        self.db_obj = orm.DBResource(**{
            'id': name,
            'name': name,
            'actions_path': metadata.get('actions_path', ''),
            'base_name': metadata.get('base_name', ''),
            'base_path': metadata.get('base_path', ''),
            'handler': metadata.get('handler', ''),
            'puppet_module': metadata.get('puppet_module', ''),
            'version': metadata.get('version', ''),
            'meta_inputs': metadata.get('input', {})
        })
        self.db_obj.save()

        self.create_inputs(args)

    # Load
    @dispatch(orm.DBResource)
    def __init__(self, resource_db):
        self.db_obj = resource_db
        self.name = resource_db.name
        # TODO: tags
        self.tags = []
        self.virtual_resource = None

    @property
    def actions(self):
        ret = {
            os.path.splitext(p)[0]: os.path.join(
                self.db_obj.actions_path, p
            )
            for p in os.listdir(self.db_obj.actions_path)
        }

        return {
            k: v for k, v in ret.items() if os.path.isfile(v)
        }

    def create_inputs(self, args=None):
        args = args or {}
        for name, v in self.db_obj.meta_inputs.items():
            value = args.get(name, v.get('value'))

            self.db_obj.add_input(name, v['schema'], value)

    @property
    def args(self):
        ret = {}
        for i in self.resource_inputs().values():
            ret[i.name] = i.backtrack_value()
        return ret

    def update(self, args):
        # TODO: disconnect input when it is updated and end_node
        #       for some input_to_input relation
        resource_inputs = self.resource_inputs()

        for k, v in args.items():
            i = resource_inputs[k]
            i.value = v
            i.save()

    def resource_inputs(self):
        return {
            i.name: i for i in self.db_obj.inputs.value
        }

    def to_dict(self):
        ret = self.db_obj.to_dict()
        ret['input'] = {}
        for k, v in self.args.items():
            ret['input'][k] = {
                'value': v,
            }

        return ret

    def color_repr(self):
        import click

        arg_color = 'yellow'

        return ("{resource_s}({name_s}='{id}', {base_path_s}={base_path} "
                "{args_s}={input}, {tags_s}={tags})").format(
            resource_s=click.style('Resource', fg='white', bold=True),
            name_s=click.style('name', fg=arg_color, bold=True),
            base_path_s=click.style('base_path', fg=arg_color, bold=True),
            args_s=click.style('args', fg=arg_color, bold=True),
            tags_s=click.style('tags', fg=arg_color, bold=True),
            **self.to_dict()
        )


def load(name):
    r = orm.DBResource.load(name)

    if not r:
        raise Exception('Resource {} does not exist in DB'.format(name))

    return Resource(r)


# TODO
def load_all():
    return [Resource(r) for r in orm.DBResource.load_all()]


def validate_resources():
    resources = load_all()

    ret = []

    for r in resources:
        e = validation.validate_resource(r)
        if e:
            ret.append((r, e))

    return ret
