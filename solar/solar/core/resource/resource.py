from copy import deepcopy
import json
from multipledispatch import dispatch
import os

from solar.interfaces.db import get_db
from solar import utils


db = get_db()


# TODO: cycle detection?
# TODO: write this as a Cypher query? Move to DB?
def _read_input_value(input_node):
    rel = db.get_relations(dest=input_node,
                           type_=db.RELATION_TYPES.resource_input)

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

        self.metadata['id'] = name

        self.tags = tags or []
        self.virtual_resource = virtual_resource

        self.node = db.get_or_create(
            name,
            args={
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
        self.name = resource_node.properties['name']
        self.metadata = read_meta(resource_node.properties['base_path'])
        self.metadata.update(resource_node.properties)
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

            i = db.get_or_create(
                k,
                args={
                    'is_list': isinstance(v.get('schema'), list),
                    'value': json.dumps(value),
                },
                collection=db.COLLECTIONS.input
            )
            db.get_or_create_relation(
                self.node,
                i,
                args={},
                type_=db.RELATION_TYPES.resource_input
            )

    @property
    def args(self):
        return {
            k: json.loads(n.properties['value'] or 'null')
            for k, n in self.resource_inputs().items()
        }

    def update(self, args):
        # TODO: disconnect input when it is updated and and end_node
        #       for some input_to_input relation
        resource_inputs = self.resource_inputs()

        for k, v in args.items():
            i = resource_inputs[k]
            i.properties['value'] = json.dumps(v)
            i.push()

    def resource_inputs(self):
        if not hasattr(self, '__resource_inputs'):
            self.__resource_inputs = [
                r.end_node for r in
                db.get_relations(source=self.node,
                                 type_=db.RELATION_TYPES.resource_input)
            ]

        for r in self.__resource_inputs:
            r.pull()

        return {
            i.properties['name']: i for i in self.__resource_inputs
        }


def load(name):
    r = db.get(name, collection=db.COLLECTIONS.resource)

    if not r:
        raise Exception('Resource {} does not exist in DB'.format(name))

    return wrap_resource(r)


def wrap_resource(resource_node):
    return Resource(resource_node)

