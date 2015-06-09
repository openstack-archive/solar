from enum import Enum
import json
import redis

from solar import utils
from solar import errors


class RedisDB(object):
    COLLECTIONS = Enum(
        'Collections',
        'connection resource state_data state_log'
    )
    DB = {
        'host': 'localhost',
        'port': 6379,
    }

    def __init__(self):
        self._r = redis.StrictRedis(**self.DB)
        self.entities = {}

    def read(self, uid, collection=COLLECTIONS.resource):
        try:
            return json.loads(
                self._r.get(self._make_key(collection.name, uid))
            )
        except TypeError:
            return None

    def save(self, uid, data, collection=COLLECTIONS.resource):
        return self._r.set(
            self._make_key(collection.name, uid),
            json.dumps(data)
        )

    def delete(self, uid, collection):
        return self._r.delete(self._make_key(collection, uid))

    def get_list(self, collection=COLLECTIONS.resource):
        key_glob = self._make_key(collection.name, '*')

        for key in self._r.keys(key_glob):
            yield json.loads(self._r.get(key))

    def clear(self):
        self._r.flushdb()

    def _make_key(self, collection, _id):
        return '{0}:{1}'.format(collection, _id)
