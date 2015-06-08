from enum import Enum
import json
import redis

from solar import utils
from solar import errors


class RedisDB(object):
    COLLECTIONS = Enum(
        'Collections',
        'connection resource'
    )
    DB = {
        'host': 'localhost',
        'port': 6379,
    }

    def __init__(self):
        self._r = redis.StrictRedis(**self.DB)
        self.entities = {}

    def read(self, uid, collection_name=COLLECTIONS.resource):
        return json.loads(
            self._r.get(self._make_key(collection_name, uid))
        )

    def save(self, uid, data, collection_name=COLLECTIONS.resource):
        return self._r.set(
            self._make_key(collection_name, uid),
            json.dumps(data)
        )

    def get_list(self, collection_name=COLLECTIONS.resource):
        key_glob = self._make_key(collection_name, '*')

        for key in self._r.keys(key_glob):
            yield json.loads(self._r.get(key))

    def clear(self):
        self._r.flushdb()

    def _make_key(self, collection, _id):
        return '{0}-{1}'.format(collection, _id)
