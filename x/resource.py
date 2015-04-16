# -*- coding: UTF-8 -*-
import os
import shutil

import yaml

import actions
import signals
import db

from x import utils


class Resource(object):
    def __init__(self, name, metadata, args, base_dir):
        self.name = name
        self.base_dir = base_dir
        self.metadata = metadata
        self.actions = metadata['actions'].keys() if metadata['actions'] else None
        self.requires = metadata['input'].keys()
        self._validate_args(args)
        self.args = args
        self.changed = []

    def __repr__(self):
        return "Resource('name={0}', metadata={1}, args={2}, base_dir='{3}')".format(self.name,
                                                                                     self.metadata,
                                                                                     self.args,
                                                                                     self.base_dir)

    def update(self, args):
        for key, value in args.iteritems():
            resource_key = self.args.get(key, None)
            if resource_key:
                self.args[key] = value
                self.changed.append(key)
                signals.notify(self, key, value)

    def action(self, action):
        if action in self.actions:
            actions.resource_action(self, action)
        else:
            raise Exception('Uuups, action is not available')

    def _validate_args(self, args):
        for req in self.requires:
            if req not in args:
                raise Exception('Requirement `{0}` is missing in args'.format(req))


def create(name, base_path, dest_path, args, connections={}):
    if not os.path.exists(base_path):
        raise Exception('Base resource does not exist: {0}'.format(dest_path))
    if not os.path.exists(dest_path):
        raise Exception('Dest dir does not exist: {0}'.format(dest_path))
    if not os.path.isdir(dest_path):
        raise Exception('Dest path is not a directory: {0}'.format(dest_path))

    dest_path = os.path.join(dest_path, name)
    base_meta_file = os.path.join(base_path, 'meta.yaml')
    meta_file = os.path.join(dest_path, 'meta.yaml')
    actions_path = os.path.join(base_path, 'actions')

    meta = yaml.load(open(base_meta_file).read())
    meta['id'] = name
    meta['version'] = '1.0.0'
    meta['actions'] = {}
    meta['input'] = args

    if os.path.exists(actions_path):
        for f in os.listdir(actions_path):
            meta['actions'][os.path.splitext(f)[0]] = f

    resource = Resource(name, meta, args, dest_path)
    signals.assign_connections(resource, connections)

    #save
    shutil.copytree(base_path, dest_path)
    with open(meta_file, 'w') as f:
        f.write(yaml.dump(meta))
    db.resource_add(name, resource)
    return resource


def load(dest_path):
    meta_file = os.path.join(dest_path, 'meta.yaml')
    meta = utils.load_file(meta_file)
    name = meta['id']
    args = meta['input']

    return Resource(name, meta, args, dest_path)

