from solar.third_party.dir_dbm import DirDBM


import os
from fnmatch import fnmatch
from copy import deepcopy

import yaml

from solar import utils
from solar import errors


def get_files(path, pattern):
    for root, dirs, files in os.walk(path):
        for file_name in files:
            if fnmatch(file_name, pattern):
                yield os.path.join(root, file_name)


class FileSystemDB(DirDBM):
    RESOURCES_PATH = './schema/resources'
    STORAGE_PATH = 'tmp/storage/'

    def __init__(self):
        utils.create_dir(self.STORAGE_PATH)
        super(FileSystemDB, self).__init__(self.STORAGE_PATH)
        self.entities = {}

    def create_resource(self, resource, tags):
        self.from_files(self.RESOURCES_PATH)

        resource_uid = '{0}_{1}'.format(resource, '_'.join(tags))
        data = deepcopy(self.get(resource))
        data['tags'] = tags
        self[resource_uid] = utils.yaml_dump(data)

    def get_copy(self, key):
        return yaml.load(deepcopy(self[key]))

    def add(self, obj):
        if 'id' in obj:
            self.entities[obj['id']] = obj

    def store_from_file(self, file_path):
        self.store(utils.load_yaml(file_path))

    def store(self, obj):
        if 'id' in obj:
            self[obj['id']] = utils.yaml_dump(obj)
        else:
            raise errors.CannotFindID('Cannot find id for object {0}'.format(obj))

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
