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
    RESOURCES_PATH = utils.read_config()['file-system-db']['resources-path']
    STORAGE_PATH = utils.read_config()['file-system-db']['storage-path']

    def __init__(self):
        utils.create_dir(self.STORAGE_PATH)
        super(FileSystemDB, self).__init__(self.STORAGE_PATH)
        self.entities = {}

    def create_resource(self, resource, tags):
        self.from_files(self.RESOURCES_PATH)

        resource_uid = '{0}_{1}'.format(resource, '_'.join(tags))
        data = deepcopy(self.get(resource))
        data['tags'] = tags
        self[resource_uid] = data

    def get_copy(self, key):
        return deepcopy(self[key])

    def add(self, obj):
        if 'id' in obj:
            self.entities[obj['id']] = obj

    def store_from_file(self, file_path):
        self.store(file_path)

    def store(self, collection, obj):
        if 'id' in obj:
            self[self._make_key(collection, obj['id'])] = obj
        else:
            raise errors.CannotFindID('Cannot find id for object {0}'.format(obj))

    def store_list(self, collection, objs):
        for obj in objs:
            self.store(collection, obj)

    def get_list(self, collection):
        collection_keys = filter(
            lambda k: k.startswith('{0}-'.format(collection)),
            self.keys())

        return map(lambda k: self[k], collection_keys)

    def get_record(self, collection, _id):
        key = self._make_key(collection, _id)
        if key not in self:
            return None

        return self[key]

    def _make_key(self, collection, _id):
        return '{0}-{1}'.format(collection, _id)

    def add_resource(self, resource):
        if 'id' in resource:
            self.entities[resource['id']] = resource

    def get(self, resource_id):
        return self.entities[resource_id]

    def from_files(self, path):
        for file_path in get_files(path, '*.yml'):
            with open(file_path) as f:
                entity = f

            self.add_resource(entity)

    def _readFile(self, path):
        return yaml.load(super(FileSystemDB, self)._readFile(path))

    def _writeFile(self, path, data):
        return super(FileSystemDB, self)._writeFile(path, utils.yaml_dump(data))

    def _encode(self, key):
        """Override method of the parent not to use base64 as a key for encoding"""
        return key

    def _decode(self, key):
        """Override method of the parent not to use base64 as a key for encoding"""
        return key
