import json
from copy import deepcopy
import py2neo

from solar.core import log

from .base import BaseGraphDB, Node, Relation


class Neo4jDB(BaseGraphDB):
    DB = {
        'host': 'localhost',
        'port': 7474,
    }
    NEO4J_CLIENT = py2neo.Graph

    def __init__(self):
        self._r = self.NEO4J_CLIENT('http://{host}:{port}/db/data/'.format(
            **self.DB
        ))

    def node_db_to_object(self, node_db):
        return Node(
            self,
            node_db.properties['name'],
            node_db.labels,
            # Neo4j Node.properties is some strange PropertySet, use dict instead
            dict(**node_db.properties)
        )

    def relation_db_to_object(self, relation_db):
        return Relation(
            self,
            self.node_db_to_object(relation_db.start_node),
            self.node_db_to_object(relation_db.end_node),
            relation_db.properties
        )

    def all(self, collection=BaseGraphDB.DEFAULT_COLLECTION):
        return [
            r.n for r in self._r.cypher.execute(
                'MATCH (n:%(collection)s) RETURN n' % {
                    'collection': collection.name,
                }
            )
        ]

    def all_relations(self, type_=BaseGraphDB.DEFAULT_RELATION):
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

    def clear_collection(self, collection=BaseGraphDB.DEFAULT_COLLECTION):
        log.log.debug('Clearing collection %s', collection.name)

        # TODO: make single DELETE query
        self._r.delete([r.n for r in self.all(collection=collection)])

    def create(self, name, properties={}, collection=BaseGraphDB.DEFAULT_COLLECTION):
        log.log.debug(
            'Creating %s, name %s with properties %s',
            collection.name,
            name,
            properties
        )

        properties = deepcopy(properties)
        properties['name'] = name

        n = py2neo.Node(collection.name, **properties)
        return self._r.create(n)[0]

    def create_relation(self,
                        source,
                        dest,
                        properties={},
                        type_=BaseGraphDB.DEFAULT_RELATION):
        log.log.debug(
            'Creating %s from %s to %s with properties %s',
            type_.name,
            source.properties['name'],
            dest.properties['name'],
            properties
        )
        s = self.get(
            source.properties['name'],
            collection=source.collection,
            db_convert=False
        )
        d = self.get(
            dest.properties['name'],
            collection=dest.collection,
            db_convert=False
        )
        r = py2neo.Relationship(s, type_.name, d, **properties)
        self._r.create(r)

        return r

    def _get_query(self, name, collection=BaseGraphDB.DEFAULT_COLLECTION):
        return 'MATCH (n:%(collection)s {name:{name}}) RETURN n' % {
            'collection': collection.name,
        }, {
            'name': name,
        }

    def get(self, name, collection=BaseGraphDB.DEFAULT_COLLECTION):
        query, kwargs = self._get_query(name, collection=collection)
        res = self._r.cypher.execute(query, kwargs)

        if res:
            return res[0].n

    def get_or_create(self,
                      name,
                      properties={},
                      collection=BaseGraphDB.DEFAULT_COLLECTION):
        n = self.get(name, collection=collection, db_convert=False)

        if n:
            if properties != n.properties:
                n.properties.update(properties)
                n.push()
            return n

        return self.create(name, properties=properties, collection=collection)

    def _relations_query(self,
                         source=None,
                         dest=None,
                         type_=BaseGraphDB.DEFAULT_RELATION,
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

    def delete_relations(self,
                         source=None,
                         dest=None,
                         type_=BaseGraphDB.DEFAULT_RELATION):
        query, kwargs = self._relations_query(
            source=source, dest=dest, type_=type_, query_type='DELETE'
        )

        self._r.cypher.execute(query, kwargs)

    def get_relations(self,
                      source=None,
                      dest=None,
                      type_=BaseGraphDB.DEFAULT_RELATION):
        query, kwargs = self._relations_query(
            source=source, dest=dest, type_=type_
        )

        res = self._r.cypher.execute(query, kwargs)

        return [r.r for r in res]

    def get_relation(self, source, dest, type_=BaseGraphDB.DEFAULT_RELATION):
        rel = self.get_relations(source=source, dest=dest, type_=type_)

        if rel:
            return rel[0]

    def get_or_create_relation(self,
                               source,
                               dest,
                               properties={},
                               type_=BaseGraphDB.DEFAULT_RELATION):
        rel = self.get_relations(source=source, dest=dest, type_=type_)

        if rel:
            r = rel[0]
            if properties != r.properties:
                r.properties.update(properties)
                r.push()
            return r

        return self.create_relation(source, dest, properties=properties, type_=type_)
