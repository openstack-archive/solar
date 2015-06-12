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
                self._r.get(self._make_key(collection, uid))
            )
        except TypeError:
            return None

    def save(self, uid, data, collection=COLLECTIONS.resource):
        ret =  self._r.set(
            self._make_key(collection, uid),
            json.dumps(data)
        )

        self._r.save()

        return ret

    def save_list(self, lst, collection=COLLECTIONS.resource):
        with self._r.pipeline() as pipe:
            pipe.multi()

            for uid, data in lst:
                key = self._make_key(collection, uid)
                pipe.set(key, json.dumps(data))

            pipe.execute()

    def get_list(self, collection=COLLECTIONS.resource):
        key_glob = self._make_key(collection, '*')

        keys = self._r.keys(key_glob)

        with self._r.pipeline() as pipe:
            pipe.multi()

            values = [self._r.get(key) for key in keys]

            pipe.execute()

        for value in values:
            yield json.loads(value)

    def clear(self):
        self._r.flushdb()

    def clear_collection(self, collection=COLLECTIONS.resource):
        key_glob = self._make_key(collection, '*')

        self._r.delete(self._r.keys(key_glob))

    def delete(self, uid, collection=COLLECTIONS.resource):
        self._r.delete(self._make_key(collection, uid))

    def _make_key(self, collection, _id):
        if isinstance(collection, self.COLLECTIONS):
            collection = collection.name

        return '{0}:{1}'.format(collection, _id)
