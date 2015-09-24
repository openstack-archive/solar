import json
import redis
import fakeredis

from .base import BaseGraphDB, Node, Relation
from .redis_db import OrderedHash


class RedisGraphDB(BaseGraphDB):
    DB = {
        'host': 'localhost',
        'port': 6379,
    }
    REDIS_CLIENT = redis.StrictRedis

    def __init__(self):
        self._r = self.REDIS_CLIENT(**self.DB)
        self.entities = {}

    def node_db_to_object(self, node_db):
        if isinstance(node_db, Node):
            return node_db

        return Node(
            self,
            node_db['name'],
            [node_db['collection']],
            node_db['properties']
        )

    def relation_db_to_object(self, relation_db):
        if isinstance(relation_db, Relation):
            return relation_db

        if relation_db['type_'] == BaseGraphDB.RELATION_TYPES.input_to_input.name:
            source_collection = BaseGraphDB.COLLECTIONS.input
            dest_collection = BaseGraphDB.COLLECTIONS.input
        elif relation_db['type_'] == BaseGraphDB.RELATION_TYPES.resource_input.name:
            source_collection = BaseGraphDB.COLLECTIONS.resource
            dest_collection = BaseGraphDB.COLLECTIONS.input
        elif relation_db['type_'] == BaseGraphDB.RELATION_TYPES.resource_event.name:
            source_collection = BaseGraphDB.COLLECTIONS.resource
            dest_collection = BaseGraphDB.COLLECTIONS.events

        source = self.get(relation_db['source'], collection=source_collection)
        dest = self.get(relation_db['dest'], collection=dest_collection)

        return Relation(
            self,
            source,
            dest,
            relation_db['properties']
        )

    def all(self, collection=BaseGraphDB.DEFAULT_COLLECTION):
        """Return all elements (nodes) of type `collection`."""

        key_glob = self._make_collection_key(collection, '*')

        for result in self._all(key_glob):
            yield result

    def all_relations(self, type_=BaseGraphDB.DEFAULT_RELATION):
        """Return all relations of type `type_`."""
        key_glob = self._make_relation_key(type_, '*')
        for result in self._all(key_glob):
            yield result

    def _all(self, key_glob):
        keys = self._r.keys(key_glob)

        with self._r.pipeline() as pipe:
            pipe.multi()

            values = [self._r.get(key) for key in keys]

            pipe.execute()

        for value in values:
            yield json.loads(value)

    def clear(self):
        """Clear the whole DB."""

        self._r.flushdb()

    def clear_collection(self, collection=BaseGraphDB.DEFAULT_COLLECTION):
        """Clear all elements (nodes) of type `collection`."""

        key_glob = self._make_collection_key(collection, '*')

        self._r.delete(self._r.keys(key_glob))

    def create(self, name, properties={}, collection=BaseGraphDB.DEFAULT_COLLECTION):
        """Create element (node) with given name, properties, of type `collection`."""

        if isinstance(collection, self.COLLECTIONS):
            collection = collection.name

        properties = {
            'name': name,
            'properties': properties,
            'collection': collection,
        }

        self._r.set(
            self._make_collection_key(collection, name),
            json.dumps(properties)
        )

        return properties

    def create_relation(self,
                        source,
                        dest,
                        properties={},
                        type_=BaseGraphDB.DEFAULT_RELATION):
        """
        Create relation (connection) of type `type_` from source to dest with
        given properties.
        """
        return self.create_relation_str(
            source.uid, dest.uid, properties, type_=type_)

    def create_relation_str(self, source, dest,
                            properties={}, type_=BaseGraphDB.DEFAULT_RELATION):
        if isinstance(type_, self.RELATION_TYPES):
            type_ = type_.name

        uid = self._make_relation_uid(source, dest)

        properties = {
            'source': source,
            'dest': dest,
            'properties': properties,
            'type_': type_,
        }

        self._r.set(
            self._make_relation_key(type_, uid),
            json.dumps(properties)
        )

        return properties

    def get(self, name, collection=BaseGraphDB.DEFAULT_COLLECTION,
            return_empty=False):
        """Fetch element with given name and collection type."""

        try:
            collection_key = self._make_collection_key(collection, name)
            item = self._r.get(collection_key)
            if not item and return_empty:
                return item
            return json.loads(item)
        except TypeError:
            raise KeyError(collection_key)

    def delete(self, name, collection=BaseGraphDB.DEFAULT_COLLECTION):
        keys = self._r.keys(self._make_collection_key(collection, name))
        if keys:
            self._r.delete(*keys)

    def get_or_create(self,
                      name,
                      properties={},
                      collection=BaseGraphDB.DEFAULT_COLLECTION):
        """
        Fetch or create element (if not exists) with given name, properties of
        type `collection`.
        """

        try:
            return self.get(name, collection=collection)
        except KeyError:
            return self.create(name, properties=properties, collection=collection)

    def _relations_glob(self,
                        source=None,
                        dest=None,
                        type_=BaseGraphDB.DEFAULT_RELATION):
        if source is None:
            source = '*'
        else:
            source = source.uid
        if dest is None:
            dest = '*'
        else:
            dest = dest.uid

        return self._make_relation_key(type_, self._make_relation_uid(source, dest))

    def delete_relations(self,
                         source=None,
                         dest=None,
                         type_=BaseGraphDB.DEFAULT_RELATION,
                         has_properties=None):
        """Delete all relations of type `type_` from source to dest."""

        glob = self._relations_glob(source=source, dest=dest, type_=type_)
        keys = self._r.keys(glob)

        if not keys:
            return

        if not has_properties:
            self._r.delete(*keys)

        rels = self.get_relations(
            source=source, dest=dest, type_=type_, has_properties=has_properties
        )
        for r in rels:
            self.delete_relations(
                source=r.start_node,
                dest=r.end_node,
                type_=type_
            )

    def get_relations(self,
                      source=None,
                      dest=None,
                      type_=BaseGraphDB.DEFAULT_RELATION,
                      has_properties=None):
        """Fetch all relations of type `type_` from source to dest."""

        glob = self._relations_glob(source=source, dest=dest, type_=type_)

        def check_has_properties(r):
            if has_properties:
                for k, v in has_properties.items():
                    if not r['properties'].get(k) == v:
                        return False

            return True

        for r in self._all(glob):
            # Glob is primitive, we must filter stuff correctly here
            if source and r['source'] != source.uid:
                continue
            if dest and r['dest'] != dest.uid:
                continue
            if not check_has_properties(r):
                continue
            yield r

    def get_relation(self, source, dest, type_=BaseGraphDB.DEFAULT_RELATION):
        """Fetch relations with given source, dest and type_."""

        uid = self._make_relation_key(source.uid, dest.uid)
        try:
            return json.loads(
                self._r.get(self._make_relation_key(type_, uid))
            )
        except TypeError:
            raise KeyError

    def get_or_create_relation(self,
                               source,
                               dest,
                               properties=None,
                               type_=BaseGraphDB.DEFAULT_RELATION):
        """Fetch or create relation with given properties."""
        properties = properties or {}

        try:
            return self.get_relation(source, dest, type_=type_)
        except KeyError:
            return self.create_relation(source, dest, properties=properties, type_=type_)

    def _make_collection_key(self, collection, _id):
        if isinstance(collection, self.COLLECTIONS):
            collection = collection.name

        # NOTE: hiera-redis backend depends on this!
        return '{0}:{1}'.format(collection, _id)

    def _make_relation_uid(self, source, dest):
        """
        There can be only one relation from source to dest, that's why
        this function works.
        """

        return '{0}-{1}'.format(source, dest)

    def _make_relation_key(self, type_, _id):
        if isinstance(type_, self.RELATION_TYPES):
            type_ = type_.name

        # NOTE: hiera-redis backend depends on this!
        return '{0}:{1}'.format(type_, _id)

    def get_ordered_hash(self, collection):
        return OrderedHash(self._r, collection)


class FakeRedisGraphDB(RedisGraphDB):

    REDIS_CLIENT = fakeredis.FakeStrictRedis
