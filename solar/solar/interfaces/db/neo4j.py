import json
from copy import deepcopy
from enum import Enum
import py2neo

from solar.core import log


class Neo4jDB(object):
    COLLECTIONS = Enum(
        'Collections',
        'input resource state_data state_log'
    )
    DEFAULT_COLLECTION=COLLECTIONS.resource
    RELATION_TYPES = Enum(
        'RelationTypes',
        'input_to_input resource_input'
    )
    DEFAULT_RELATION=RELATION_TYPES.resource_input
    DB = {
        'host': 'localhost',
        'port': 7474,
    }
    NEO4J_CLIENT = py2neo.Graph

    def __init__(self):
        self._r = self.NEO4J_CLIENT('http://{host}:{port}/db/data/'.format(
            **self.DB
        ))
        self.entities = {}

    @staticmethod
    def _args_to_db(args):
        return {
            k: json.dumps(v) for k, v in args.items()
        }

    @staticmethod
    def _args_from_db(db_args):
        return {
            k: json.loads(v) for k, v in db_args.items()
        }

    @staticmethod
    def obj_to_db(o):
        o.properties = Neo4jDB._args_to_db(o.properties)

    @staticmethod
    def obj_from_db(o):
        o.properties = Neo4jDB._args_from_db(o.properties)

    def all(self, collection=DEFAULT_COLLECTION):
        return [
            r.n for r in self._r.cypher.execute(
                'MATCH (n:%(collection)s) RETURN n' % {
                    'collection': collection.name,
                }
            )
        ]

    def all_relations(self, type_=DEFAULT_RELATION):
        return [
            r.r for r in self._r.cypher.execute(
                *self._relations_query(
                    source=None, dest=None, type_=type_
                )
            )
        ]

    def clear(self):
        log.log.debug('Clearing whole DB')

        self._r.delete_all()

    def clear_collection(self, collection=DEFAULT_COLLECTION):
        log.log.debug('Clearing collection %s', collection.name)

        # TODO: make single DELETE query
        self._r.delete([r.n for r in self.all(collection=collection)])

    def create(self, name, args={}, collection=DEFAULT_COLLECTION):
        log.log.debug(
            'Creating %s, name %s with args %s',
            collection.name,
            name,
            args
        )

        properties = deepcopy(args)
        properties['name'] = name

        n = py2neo.Node(collection.name, **properties)
        self._r.create(n)

        return n

    def create_relation(self, source, dest, args={}, type_=DEFAULT_RELATION):
        log.log.debug(
            'Creating %s from %s to %s with args %s',
            type_.name,
            source.properties['name'],
            dest.properties['name'],
            args
        )
        r = py2neo.Relationship(source, type_.name, dest, **args)
        self._r.create(r)

        return r

    def get(self, name, collection=DEFAULT_COLLECTION):
        res = self._r.cypher.execute(
            'MATCH (n:%(collection)s {name:{name}}) RETURN n' % {
                'collection': collection.name,
            }, {
                'name': name,
            }
        )

        if res:
            return res[0].n

    def get_or_create(self, name, args={}, collection=DEFAULT_COLLECTION):
        n = self.get(name, collection=collection)

        if n:
            if args != n.properties:
                n.properties.update(args)
                n.push()
            return n

        return self.create(name, args=args, collection=collection)

    def _relations_query(self,
                         source=None,
                         dest=None,
                         type_=DEFAULT_RELATION,
                         query_type='RETURN'):
        kwargs = {}
        source_query = '(n)'
        if source:
            source_query = '(n {name:{source_name}})'
            kwargs['source_name'] = source.properties['name']
        dest_query = '(m)'
        if dest:
            dest_query = '(m {name:{dest_name}})'
            kwargs['dest_name'] = dest.properties['name']
        rel_query = '[r:%(type_)s]' % {'type_': type_.name}

        query = ('MATCH %(source_query)s-%(rel_query)s->'
                 '%(dest_query)s %(query_type)s r' % {
                     'dest_query': dest_query,
                     'query_type': query_type,
                     'rel_query': rel_query,
                     'source_query': source_query,
                     })

        return query, kwargs

    def delete_relations(self, source=None, dest=None, type_=DEFAULT_RELATION):
        query, kwargs = self._relations_query(
            source=source, dest=dest, type_=type_, query_type='DELETE'
        )

        self._r.cypher.execute(query, kwargs)

    def get_relations(self, source=None, dest=None, type_=DEFAULT_RELATION):
        query, kwargs = self._relations_query(
            source=source, dest=dest, type_=type_
        )

        res = self._r.cypher.execute(query, kwargs)

        return [r.r for r in res]

    def get_or_create_relation(self,
                               source,
                               dest,
                               args={},
                               type_=DEFAULT_RELATION):
        rel = self.get_relations(source=source, dest=dest, type_=type_)

        if rel:
            r = rel[0]
            if args != r.properties:
                r.properties.update(args)
                r.push()
            return r

        return self.create_relation(source, dest, args=args, type_=type_)
