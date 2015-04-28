# -*- coding: UTF-8 -*-
import copy
import json
import os
import shutil

import yaml

from x import actions
from x import db
from x import observer
from x import signals
from x import utils


class Resource(object):
    def __init__(self, name, metadata, args, base_dir, tags=None):
        self.name = name
        self.base_dir = base_dir
        self.metadata = metadata
        self.actions = metadata['actions'].keys() if metadata['actions'] else None
        self.requires = metadata['input'].keys()
        self._validate_args(args, metadata['input'])
        self.args = {}
        for arg_name, arg_value in args.items():
            type_ = metadata.get('input-types', {}).get(arg_name) or 'simple'
            self.args[arg_name] = observer.create(type_, self, arg_name, arg_value)
        self.metadata['input'] = args
        self.input_types = metadata.get('input-types', {})
        self.changed = []
        self.tags = tags or []

    def __repr__(self):
        return ("Resource(name='{0}', metadata={1}, args={2}, "
                "base_dir='{3}', tags={4})").format(self.name,
                                                    json.dumps(self.metadata),
                                                    json.dumps(self.args_show()),
                                                    self.base_dir,
                                                    self.tags)

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

    def _validate_args(self, args, inputs):
        for req in self.requires:
            if req not in args:
                # If metadata input is filled with a value, use it as default
                # and don't report an error
                if inputs.get(req):
                    args[req] = inputs[req]
                else:
                    raise Exception('Requirement `{0}` is missing in args'.format(req))

    # TODO: versioning
    def save(self):
        metadata = copy.deepcopy(self.metadata)

        metadata['tags'] = self.tags
        metadata['input'] = self.args_dict()

        meta_file = os.path.join(self.base_dir, 'meta.yaml')
        with open(meta_file, 'w') as f:
            f.write(yaml.dump(metadata))
            f.write(yaml.dump(metadata, default_flow_style=False))


def create(name, base_path, dest_path, args, connections={}):
    if not os.path.exists(base_path):
        raise Exception('Base resource does not exist: {0}'.format(dest_path))
    if not os.path.exists(dest_path):
        raise Exception('Dest dir does not exist: {0}'.format(dest_path))
    if not os.path.isdir(dest_path):
        raise Exception('Dest path is not a directory: {0}'.format(dest_path))

    dest_path = os.path.join(dest_path, name)
    base_meta_file = os.path.join(base_path, 'meta.yaml')
    actions_path = os.path.join(base_path, 'actions')

    meta = yaml.load(open(base_meta_file).read())
    meta['id'] = name
    meta['version'] = '1.0.0'
    meta['actions'] = {}
    meta['tags'] = []

    if os.path.exists(actions_path):
        for f in os.listdir(actions_path):
            meta['actions'][os.path.splitext(f)[0]] = f

    resource = Resource(name, meta, args, dest_path)
    signals.assign_connections(resource, connections)

    # save
    shutil.copytree(base_path, dest_path)
    resource.save()
    db.resource_add(name, resource)

    return resource


def load(dest_path):
    meta_file = os.path.join(dest_path, 'meta.yaml')
    meta = utils.load_file(meta_file)
    name = meta['id']
    args = meta['input']
    tags = meta.get('tags', [])

    resource = Resource(name, meta, args, dest_path, tags=tags)

    db.resource_add(name, resource)

    return resource


def load_all(dest_path):
    ret = {}

    for name in os.listdir(dest_path):
        resource_path = os.path.join(dest_path, name)
        resource = load(resource_path)
        ret[resource.name] = resource

    signals.Connections.reconnect_all()

    return ret
