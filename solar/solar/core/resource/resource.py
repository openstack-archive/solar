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
from solar import utils


db = get_db()


# TODO: cycle detection?
# TODO: write this as a Cypher query? Move to DB?
def _read_input_value(input_node):
    rel = db.get_relations(dest=input_node,
                           type_=db.RELATION_TYPES.input_to_input)

    if not rel:
        v = input_node.properties['value'] or 'null'
        return json.loads(v)

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

        self.metadata['id'] = name

        self.tags = tags or []
        self.virtual_resource = virtual_resource

        self.node = db.create(
            name,
            properties={
                'actions_path': self.metadata.get('actions_path', ''),
                'base_name': self.metadata.get('base_name', ''),
                'base_path': self.metadata.get('base_path', ''),
                'handler': self.metadata.get('handler', ''),
                'id': self.metadata['id'],
                'version': self.metadata.get('version', ''),
            },
            collection=db.COLLECTIONS.resource
        )

        self.set_args_from_dict(args)

    # Load
    @dispatch(object)
    def __init__(self, resource_node):
        self.node = resource_node
        self.name = resource_node.uid
        self.metadata = resource_node.properties
        self.tags = []
        self.virtual_resource = None

    @property
    def actions(self):
        return self.metadata.get('actions') or []

    # TODO: json.dumps/loads should be probably moved to neo4j.py
    def set_args_from_dict(self, args):
        self.node.pull()

        for k, v in self.metadata['input'].items():
            value = args.get(k, v.get('value'))

            uid = '{}-{}'.format(k, uuid.uuid4())

            i = db.get_or_create(
                uid,
                properties={
                    'is_list': isinstance(v.get('schema'), list),
                    'input_name': k,
                    'value': json.dumps(value),
                },
                collection=db.COLLECTIONS.input
            )
            db.get_or_create_relation(
                self.node,
                i,
                properties={},
                type_=db.RELATION_TYPES.resource_input
            )

    @property
    def args(self):
        ret = {}
        for k, n in self.resource_inputs().items():
            ret[k] = _read_input_value(n)
        return ret

    def update(self, args):
        # TODO: disconnect input when it is updated and and end_node
        #       for some input_to_input relation
        resource_inputs = self.resource_inputs()

        for k, v in args.items():
            i = resource_inputs[k]
            i.properties['value'] = json.dumps(v)
            i.push()

    def resource_inputs(self):
        resource_inputs = [
            r.end_node for r in
            db.get_relations(source=self.node,
                             type_=db.RELATION_TYPES.resource_input)
        ]

        return {
            i.properties['input_name']: i for i in resource_inputs
        }


def load(name):
    r = db.get(name, collection=db.COLLECTIONS.resource)

    if not r:
        raise Exception('Resource {} does not exist in DB'.format(name))

    return wrap_resource(r)


def wrap_resource(resource_node):
    return Resource(resource_node)
