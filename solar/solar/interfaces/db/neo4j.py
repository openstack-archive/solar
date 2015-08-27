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
                'MATCH (n)-[r:%(type_)s]->(m) RETURN r' % {
                    'type_': type_.name,
                }
            )
        ]

    def clear(self):
        self._r.delete_all()

    def clear_collection(self, collection=DEFAULT_COLLECTION):
        self._r.delete([r.n for r in self.all(collection=collection)])

    def create(self, name, args={}, collection=DEFAULT_COLLECTION):
        log.log.debug('Neo4j Creating %s with args %s', name, args)

        properties = deepcopy(args)
        properties['name'] = name

        n = py2neo.Node(collection.name, **properties)
        self._r.create(n)

        return n

    def create_relation(self, source, dest, args={}, type_=DEFAULT_RELATION):
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
            n.properties.update(args)
            n.push()
            return n

        return self.create(name, args=args, collection=collection)

    def get_relations(self, source=None, dest=None, type_=DEFAULT_RELATION):
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
                 '%(dest_query)s RETURN r' % {
                    'dest_query': dest_query,
                    'rel_query': rel_query,
                    'source_query': source_query,
                 })

        res = self._r.cypher.execute(query, kwargs)

        relations = [r.r for r in res]
        for r in relations:
            r.start_node.pull()
            r.end_node.pull()

        return relations

    def get_or_create_relation(self,
                               source,
                               dest,
                               args={},
                               type_=DEFAULT_RELATION):
        # TODO: remove relation if dest node is an input of simple type
        rel = self.get_relations(source=source, dest=dest, type_=type_)

        if rel:
            r = rel[0]
            r.properties.update(args)
            r.push()
            return r

        return self.create_relation(source, dest, args=args, type_=type_)
