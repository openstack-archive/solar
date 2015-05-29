# -*- coding: utf-8 -*-
import copy
import os

from copy import deepcopy

import yaml

import solar

from solar.core import actions
from solar.core import observer
from solar.core import signals
from solar import utils
from solar.core import validation

from solar.core.connections import ResourcesConnectionGraph
from solar.interfaces.db import get_db

db = get_db()


class Resource(object):
    def __init__(self, name, metadata, args, tags=None):
        self.name = name
        self.metadata = metadata
        self.actions = metadata['actions'].keys() if metadata['actions'] else None
        self.args = {}

        for arg_name, arg_value in args.items():
            if not self.metadata['input'].get(arg_name):
                continue

            metadata_arg = self.metadata['input'][arg_name]
            type_ = validation.schema_input_type(metadata_arg.get('schema', 'str'))

            value = arg_value
            if not value and metadata_arg['value']:
                value = metadata_arg['value']

            self.args[arg_name] = observer.create(type_, self, arg_name, value)
        self.changed = []
        self.tags = tags or []

    def __repr__(self):
        return ("Resource(name='{name}', metadata={metadata}, args={args}, "
                "tags={tags})").format(**self.to_dict())

    def to_dict(self):
        return {
            'name': self.name,
            'metadata': self.metadata,
            'args': self.args_show(),
            'tags': self.tags,
        }

    def args_show(self):
        def formatter(v):
            if isinstance(v, observer.ListObserver):
                return v.value
            elif isinstance(v, observer.Observer):
                return {
                    'emitter': v.emitter.attached_to.name if v.emitter else None,
                    'value': v.value,
                }

            return v

        return {k: formatter(v) for k, v in self.args.items()}

    def args_dict(self):
        return {k: v.value for k, v in self.args.items()}

    def add_tag(self, tag):
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag):
        try:
            self.tags.remove(tag)
        except ValueError:
            pass

    def notify(self, emitter):
        """Update resource's args from emitter's args.

        :param emitter: Resource
        :return:
        """
        for key, value in emitter.args.iteritems():
            self.args[key].notify(value)

    def update(self, args):
        """This method updates resource's args with a simple dict.

        :param args:
        :return:
        """
        # Update will be blocked if this resource is listening
        # on some input that is to be updated -- we should only listen
        # to the emitter and not be able to change the input's value

        for key, value in args.iteritems():
            self.args[key].update(value)

    def action(self, action):
        if action in self.actions:
            actions.resource_action(self, action)
        else:
            raise Exception('Uuups, action is not available')

    # TODO: versioning
    def save(self):
        metadata = copy.deepcopy(self.metadata)

        metadata['tags'] = self.tags
        for k, v in self.args_dict().items():
            metadata['input'][k]['value'] = v

        db.add_resource(self.name, metadata)
        meta_file = os.path.join(self.base_dir, 'meta.yaml')
        utils.yaml_dump_to(metadata, meta_file)


def create(name, base_path, args, tags=[], connections={}):
    if not os.path.exists(base_path):
        raise Exception('Base resource does not exist: {0}'.format(base_path))

    base_meta_file = os.path.join(base_path, 'meta.yaml')
    actions_path = os.path.join(base_path, 'actions')

    meta = utils.yaml_load(base_meta_file)
    meta['id'] = name
    meta['version'] = '1.0.0'
    meta['actions'] = {}
    meta['actions_path'] = actions_path
    meta['base_path'] = os.path.abspath(base_path)

    if os.path.exists(actions_path):
        for f in os.listdir(actions_path):
            meta['actions'][os.path.splitext(f)[0]] = f

    resource = Resource(name, meta, args, tags=tags)
    signals.assign_connections(resource, connections)
    resource.save()

    return resource


def wrap_resource(raw_resource):
    name = raw_resource['id']
    args = {k: v['value'] for k, v in raw_resource['input'].items()}
    tags = raw_resource.get('tags', [])

    return Resource(name, raw_resource, args, tags=tags)


def load_all():
    ret = {}

    for raw_resource in db.get_list('resource'):
        resource = wrap_resource(raw_resource)
        ret[resource.name] = resource

    signals.Connections.reconnect_all()

    return ret


def assign_resources_to_nodes(resources, nodes):
    for node in nodes:
        for resource in resources:
            res = deepcopy(resource)
            res['tags'] = list(set(node.get('tags', [])) |
                               set(resource.get('tags', [])))
            resource_uuid = solar.utils.generate_uuid()
            # We should not generate here any uuid's, because
            # a single node should be represented with a single
            # resource
            node_uuid = node['id']

            node_resource_template = solar.utils.read_config()['node_resource_template']
            created_resource = create(resource_uuid, resource['dir_path'], res['input'], tags=res['tags'])
            created_node = create(node_uuid, node_resource_template, node, tags=node.get('tags', []))

            signals.connect(created_node, created_resource)


def connect_resources(profile):
    connections = profile.get('connections', [])
    graph = ResourcesConnectionGraph(connections, load_all().values())

    for connection in graph.iter_connections():
        signals.connect(connection['from'], connection['to'], connection['mapping'])
