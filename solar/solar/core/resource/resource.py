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
import json
from multipledispatch import dispatch
import os
import uuid

from solar.interfaces.db import get_db
from solar.interfaces import orm
from solar import utils


db = get_db()


# TODO: this is actually just fetching head element in linked list
#       so this whole algorithm can be moved to the db backend probably
# TODO: cycle detection?
# TODO: write this as a Cypher query? Move to DB?
def _read_input_value(input_node):
    rel = db.get_relations(dest=input_node,
                           type_=db.RELATION_TYPES.input_to_input)

    if not rel:
        return input_node.properties['value']

    if input_node.properties['is_list']:
        return [_read_input_value(r.start_node) for r in rel]

    return _read_input_value(rel[0].start_node)


def prepare_meta(meta):
    actions_path = os.path.join(meta['base_path'], 'actions')
    meta['actions_path'] = actions_path
    meta['base_name'] = os.path.split(meta['base_path'])[-1]

    meta['actions'] = {}
    if os.path.exists(meta['actions_path']):
        for f in os.listdir(meta['actions_path']):
            meta['actions'][os.path.splitext(f)[0]] = f


def read_meta(base_path):
    base_meta_file = os.path.join(base_path, 'meta.yaml')

    metadata = utils.yaml_load(base_meta_file)
    metadata['version'] = '1.0.0'
    metadata['base_path'] = os.path.abspath(base_path)

    return metadata


class Resource(object):
    _metadata = {}

    # Create
    @dispatch(str, str, dict)
    def __init__(self, name, base_path, args, tags=None, virtual_resource=None):
        self.name = name
        if base_path:
            self.metadata = read_meta(base_path)
        else:
            self.metadata = deepcopy(self._metadata)

        self.tags = tags or []
        self.virtual_resource = virtual_resource

        self.db_obj = orm.DBResource(**{
            'id': name,
            'name': name,
            'actions_path': self.metadata.get('actions_path', ''),
            'base_name': self.metadata.get('base_name', ''),
            'base_path': self.metadata.get('base_path', ''),
            'handler': self.metadata.get('handler', ''),
            'version': self.metadata.get('version', ''),
            'meta_inputs': self.metadata.get('input', {})
        })
        self.db_obj.save()

        self.create_inputs(args)

    # Load
    @dispatch(orm.DBResource)
    def __init__(self, resource_db):
        self.db_obj = resource_db
        self.name = resource_db.name
        # TODO:
        self.tags = []
        self.virtual_resource = None

    @property
    def actions(self):
        return self.resource_db.actions or []

    # TODO: json.dumps/loads should be probably moved to neo4j.py
    def create_inputs(self, args):
        for name, v in self.db_obj.meta_inputs.items():
            value = args.get(name, v.get('value'))

            self.db_obj.add_input(name, v['schema'], value)

    @property
    def args(self):
        ret = {}
        for i in self.resource_inputs().values():
            ret[i.name] = _read_input_value(i._db_node)
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


def load(name):
    r = orm.DBResource.load(name)

    if not r:
        raise Exception('Resource {} does not exist in DB'.format(name))

    return Resource(r)
