from solar.third_party.dir_dbm import DirDBM

import atexit
import os
import types
import yaml

from solar import utils
from solar import errors


class CachedFileSystemDB(DirDBM):
    STORAGE_PATH = utils.read_config()['file-system-db']['storage-path']
    RESOURCE_COLLECTION_NAME = 'resource'

    _CACHE = {}

    def __init__(self):
        utils.create_dir(self.STORAGE_PATH)
        super(CachedFileSystemDB, self).__init__(self.STORAGE_PATH)
        self.entities = {}

        atexit.register(self.flush)

    def __setitem__(self, k, v):
        """
        C{dirdbm[k] = v}
        Create or modify a textfile in this directory
        @type k: strings        @param k: key to setitem
        @type v: strings        @param v: value to associate with C{k}
        """
        assert type(k) == types.StringType, "DirDBM key must be a string"
        # NOTE: Can be not a string if _writeFile in the child is redefined
        # assert type(v) == types.StringType, "DirDBM value must be a string"
        k = self._encode(k)

        # we create a new file with extension .new, write the data to it, and
        # if the write succeeds delete the old file and rename the new one.
        old = os.path.join(self.dname, k)
        try:
            self._writeFile(old, v)
        except:
            raise

    def get_resource(self, uid):
        return self[self._make_key(self.RESOURCE_COLLECTION_NAME, uid)]

    def get_obj_resource(self, uid):
        from solar.core.resource import wrap_resource
        raw_resource = self[self._make_key(self.RESOURCE_COLLECTION_NAME, uid)]

        return wrap_resource(raw_resource)

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
        if path not in self._CACHE:
            data = yaml.load(super(CachedFileSystemDB, self)._readFile(path))
            self._CACHE[path] = data
            return data

        return self._CACHE[path]

    def _writeFile(self, path, data):
        self._CACHE[path] = data

    def _encode(self, key):
        """Override method of the parent not to use base64 as a key for encoding"""
        return key

    def _decode(self, key):
        """Override method of the parent not to use base64 as a key for encoding"""
        return key

    def flush(self):
        print 'FLUSHING DB'
        for path, data in self._CACHE.items():
            super(CachedFileSystemDB, self)._writeFile(path, yaml.dump(data))
