# -*- coding: utf-8 -*-
import os

from copy import deepcopy

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

        self.tags = tags or []
        self.set_args_from_dict(args)

    @property
    def actions(self):
        return self.metadata.get('actions') or []

    @property
    def args(self):
        ret = {}

        args = self.args_dict()

        for arg_name, metadata_arg in self.metadata['input'].items():
            type_ = validation.schema_input_type(metadata_arg.get('schema', 'str'))

            ret[arg_name] = observer.create(
                type_, self, arg_name, args.get(arg_name)
            )

        return ret

    def args_dict(self):
        raw_resource = db.read(self.name, collection=db.COLLECTIONS.resource)
        if raw_resource is None:
            return {}

        self.metadata = raw_resource

        args = self.metadata['input']

        return {k: v['value'] for k, v in args.items()}

    def set_args_from_dict(self, new_args):
        args = self.args_dict()
        args.update(new_args)

        self.metadata['tags'] = self.tags
        for k, v in args.items():
            if k not in self.metadata['input']:
                raise NotImplementedError(
                    'Argument {} not implemented for resource {}'.format(k, self)
                )

            self.metadata['input'][k]['value'] = v

        db.save(self.name, self.metadata, collection=db.COLLECTIONS.resource)

    def set_args(self, args):
        self.set_args_from_dict({k: v.value for k, v in args.items()})

    def __repr__(self):
        return ("Resource(name='{id}', metadata={metadata}, args={input}, "
                "tags={tags})").format(**self.to_dict())

    def color_repr(self):
        import click

        arg_color = 'yellow'

        return ("{resource_s}({name_s}='{id}', {metadata_s}={metadata}, "
                "{args_s}={input}, {tags_s}={tags})").format(
            resource_s=click.style('Resource', fg='white', bold=True),
            name_s=click.style('name', fg=arg_color, bold=True),
            metadata_s=click.style('metadata', fg=arg_color, bold=True),
            args_s=click.style('args', fg=arg_color, bold=True),
            tags_s=click.style('tags', fg=arg_color, bold=True),
            **self.to_dict()
        )

    def to_dict(self):
        return {
            'id': self.name,
            'metadata': self.metadata,
            'input': self.args_show(),
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
        r_args = self.args

        for key, value in emitter.args.iteritems():
            r_args[key].notify(value)

    def update(self, args):
        """This method updates resource's args with a simple dict.

        :param args:
        :return:
        """
        # Update will be blocked if this resource is listening
        # on some input that is to be updated -- we should only listen
        # to the emitter and not be able to change the input's value
        r_args = self.args

        for key, value in args.iteritems():
            r_args[key].update(value)

        self.set_args(r_args)

    def action(self, action):
        if action in self.actions:
            actions.resource_action(self, action)
        else:
            raise Exception('Uuups, action is not available')


def create(name, base_path, args, tags=[], connections={}):
    from solar.core import resource_provider

    if isinstance(base_path, resource_provider.BaseProvider):
        base_path = base_path.directory

    if not os.path.exists(base_path):
        raise Exception(
            'Base resource does not exist: {0}'.format(base_path)
        )

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

    return resource


def wrap_resource(raw_resource):
    name = raw_resource['id']
    args = {k: v['value'] for k, v in raw_resource['input'].items()}
    tags = raw_resource.get('tags', [])

    return Resource(name, raw_resource, args, tags=tags)


def load(resource_name):
    raw_resource = db.read(resource_name, collection=db.COLLECTIONS.resource)

    if raw_resource is None:
        raise KeyError(
            'Resource {} does not exist'.format(resource_name)
        )

    return wrap_resource(raw_resource)


def load_all():
    ret = {}

    for raw_resource in db.get_list(collection=db.COLLECTIONS.resource):
        resource = wrap_resource(raw_resource)
        ret[resource.name] = resource

    return ret


def assign_resources_to_nodes(resources, nodes):
    for node in nodes:
        for resource in resources:
            res = deepcopy(resource)
            res['tags'] = list(set(node.get('tags', [])) |
                               set(resource.get('tags', [])))
            resource_uuid = '{0}-{1}'.format(res['id'], solar.utils.generate_uuid())
            # We should not generate here any uuid's, because
            # a single node should be represented with a single
            # resource
            node_uuid = node['id']

            node_resource_template = solar.utils.read_config()['node_resource_template']
            args = {k: v['value'] for k, v in res['input'].items()}
            created_resource = create(resource_uuid, resource['dir_path'], args, tags=res['tags'])
            created_node = create(node_uuid, node_resource_template, node, tags=node.get('tags', []))

            signals.connect(created_node, created_resource)


def connect_resources(profile):
    connections = profile.get('connections', [])
    graph = ResourcesConnectionGraph(connections, load_all().values())

    for connection in graph.iter_connections():
        signals.connect(connection['from'], connection['to'], connection['mapping'])
