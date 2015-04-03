from solar.third_party.dir_dbm import DirDBM


import os
from fnmatch import fnmatch
from copy import deepcopy

import yaml

from solar import utils


def get_files(path, pattern):
    for root, dirs, files in os.walk(path):
        for file_name in files:
            if fnmatch(file_name, pattern):
                yield os.path.join(root, file_name)


class FileSystemDB(DirDBM):
    RESOURCES_PATH = './schema/resources'

    def __init__(self):
        utils.create_dir('tmp/created/')
        super(FileSystemDB, self).__init__('tmp/created/')
        self.entities = {}

    def create_resource(self, resource, tags):
        self.from_files(self.RESOURCES_PATH)

        resource_uid = '{0}_{1}'.format(resource, '_'.join(tags))
        data = deepcopy(self.get(resource))
        data['tags'] = tags
        self[resource_uid] = yaml.dump(data, default_flow_style=False)

    def get_copy(self, key):
        return yaml.load(deepcopy(self[key]))

    def add(self, resource):
        if 'id' in resource:
            self.entities[resource['id']] = resource

    def add_resource(self, resource):
        if 'id' in resource:
            self.entities[resource['id']] = resource

    def get(self, resource_id):
        return self.entities[resource_id]

    def from_files(self, path):
        for file_path in get_files(path, '*.yml'):
            with open(file_path) as f:
                entity = yaml.load(f)

            self.add_resource(entity)
