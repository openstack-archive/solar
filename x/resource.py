# -*- coding: UTF-8 -*-
import json
import os
import shutil

import yaml

import actions
import signals
import db

from x import utils


class Resource(object):
    def __init__(self, name, metadata, args, base_dir, tags=None):
        self.name = name
        self.base_dir = base_dir
        self.metadata = metadata
        self.actions = metadata['actions'].keys() if metadata['actions'] else None
        self.requires = metadata['input'].keys()
        self._validate_args(args, metadata['input'])
        self.args = args
        self.metadata['input'] = args
        self.input_types = metadata.get('input-types', {})
        self.changed = []
        self.tags = tags or []

    def __repr__(self):
        return ("Resource(name='{0}', metadata={1}, args={2}, "
                "base_dir='{3}', tags={4})").format(self.name,
                                                    json.dumps(self.metadata),
                                                    json.dumps(self.args),
                                                    self.base_dir,
                                                    self.tags)

    def add_tag(self, tag):
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag):
        try:
            self.tags.remove(tag)
        except ValueError:
            pass

    def update(self, args, emitter=None):
        for key, value in args.iteritems():
            if self.input_types.get(key, '') == 'list':
                if emitter is None:
                    raise Exception('I need to know the emitter when updating input of list type')
                self.args[key][emitter.name] = value
            else:
                self.args[key] = value
            self.changed.append(key)
            signals.notify(self, key, value)

        self.save()

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
        self.metadata['tags'] = self.tags

        meta_file = os.path.join(self.base_dir, 'meta.yaml')
        with open(meta_file, 'w') as f:
            f.write(yaml.dump(self.metadata, default_flow_style=False))


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

    return ret
