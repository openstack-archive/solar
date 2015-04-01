
import os
from fnmatch import fnmatch

import yaml


def get_files(path, pattern):
    for root, dirs, files in os.walk(path):
        for file_name in files:
            if fnmatch(file_name, pattern):
                yield os.path.join(root, file_name)


class Storage(object):

    def __init__(self):
        self.entities = {}

    def add(self, resource):
        if 'id' in resource:
            self.entities[resource['id']] = resource

    def add_resource(self, resource):
        if 'id' in resource:
            self.entities[resource['id']] = resource

    def get(self, resource_id):
        return self.entities[resource_id]

    @classmethod
    def from_files(cls, path):
        store = cls()
        for file_path in get_files(path, '*.yml'):
            with open(file_path) as f:
                entity = yaml.load(f)

            store.add_resource(entity)
        return store
