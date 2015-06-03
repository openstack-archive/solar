from solar.third_party.dir_dbm import DirDBM


import os
from fnmatch import fnmatch
from copy import deepcopy

import yaml

from solar import utils
from solar import errors


class FileSystemDB(DirDBM):
    STORAGE_PATH = utils.read_config()['file-system-db']['storage-path']
    RESOURCE_COLLECTION_NAME = 'resource'

    def __init__(self):
        utils.create_dir(self.STORAGE_PATH)
        super(FileSystemDB, self).__init__(self.STORAGE_PATH)
        self.entities = {}

    def get_resource(self, uid):
        return self[self._make_key(self.RESOURCE_COLLECTION_NAME, uid)]

    def get_obj_resource(self, uid):
        if not uid in self.entities:
            from solar.core.resource import wrap_resource
            raw_resource = self[self._make_key(self.RESOURCE_COLLECTION_NAME, uid)]
            self.entities[uid] = wrap_resource(raw_resource)
        return self.entities[uid]

    def add_resource(self, uid, resource):
        self[self._make_key(self.RESOURCE_COLLECTION_NAME, uid)] = resource

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
