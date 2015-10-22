#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import inspect
import networkx
import uuid

from solar import errors
from solar.core import validation
from solar.interfaces.db import base
from solar.interfaces.db import get_db

import os
USE_CACHE = int(os.getenv("USE_CACHE", 0))


db = get_db()


from functools import wraps

def cache_me(store):
    def _inner(f):
        @wraps(f)
        def _inner2(obj, *args, **kwargs):
            try:
                return store[obj.id]
            except KeyError:
                pass
            else:
                val = f(obj, *args, **kwargs)
                store[obj.id] = val
                return val
        if USE_CACHE:
            return _inner2
        else:
            return f
    return _inner


# def cache_me_cls(store):
#     def _inner(f):
#         @wraps(f)
#         def _inner2(cls, arg0, *args, **kwargs):
#             try:
#                 sc = store[cls.__name__]
#             except KeyError:
#                 pass
#             else:
#                 sc = store[cls.__name__] = {}
#             try:
#                 return sc[arg0]
#             except KeyError:
#                 pass
#             else:
#                 val = f(obj, *args, **kwargs)
#                 sc[arg0] = val
#                 return val
#         return _inner2
#     return _inner


class DBField(object):
    is_primary = False
    schema = None
    schema_in_field = None
    default_value = None

    def __init__(self, name, value=None):
        self.name = name
        self.value = value
        if value is None:
            self.value = self.default_value

    def __eq__(self, inst):
        return self.name == inst.name and self.value == inst.value

    def __ne__(self, inst):
        return not self.__eq__(inst)

    def __hash__(self):
        return hash('{}:{}'.format(self.name, self.value))

    def validate(self):
        if self.schema is None:
            return

        es = validation.validate_input(self.value, schema=self.schema)
        if es:
            raise errors.ValidationError('"{}": {}'.format(self.name, es[0]))


def db_field(schema=None,
             schema_in_field=None,
             default_value=None,
             is_primary=False):
    """Definition for the DB field.

    schema - simple schema according to the one in solar.core.validation
    schema_in_field - if you don't want to fix schema, you can specify
        another field in DBObject that will represent the schema used
        for validation of this field
    is_primary - only one field in db object can be primary. This key is used
        for creating key in the DB
    """

    class DBFieldX(DBField):
        pass

    DBFieldX.is_primary = is_primary
    DBFieldX.schema = schema
    DBFieldX.schema_in_field = schema_in_field
    if default_value is not None:
        DBFieldX.default_value = default_value

    return DBFieldX


class DBRelatedField(object):
    source_db_class = None
    destination_db_class = None
    relation_type = None

    def __init__(self, name, source_db_object):
        self.name = name
        self.source_db_object = source_db_object

    @classmethod
    def graph(self):
        relations = db.get_relations(type_=self.relation_type)

        g = networkx.MultiDiGraph()

        for r in relations:
            source = self.source_db_class(**r.start_node.properties)
            dest = self.destination_db_class(**r.end_node.properties)
            properties = r.properties.copy()
            g.add_edge(
                source,
                dest,
                attr_dict=properties
            )

        return g

    def all(self):
        source_db_node = self.source_db_object._db_node

        if source_db_node is None:
            return []

        return db.get_relations(source=source_db_node,
                                type_=self.relation_type)

    def all_by_dest(self, destination_db_object):
        destination_db_node = destination_db_object._db_node

        if destination_db_node is None:
            return set()

        return db.get_relations(dest=destination_db_node,
                                type_=self.relation_type)

    def add(self, *destination_db_objects):
        for dest in destination_db_objects:
            if not isinstance(dest, self.destination_db_class):
                raise errors.SolarError(
                    'Object {} is of incompatible type {}.'.format(
                        dest, self.destination_db_class
                    )
                )

            db.get_or_create_relation(
                self.source_db_object._db_node,
                dest._db_node,
                properties={},
                type_=self.relation_type
            )

    def add_hash(self, destination_db_object, destination_key, tag=None):
        if not isinstance(destination_db_object, self.destination_db_class):
            raise errors.SolarError(
                'Object {} is of incompatible type {}.'.format(
                    destination_db_object, self.destination_db_class
                )
            )

        db.get_or_create_relation(
            self.source_db_object._db_node,
            destination_db_object._db_node,
            properties={'destination_key': destination_key, 'tag': tag},
            type_=self.relation_type
        )

    def remove(self, *destination_db_objects):
        for dest in destination_db_objects:
            db.delete_relations(
                source=self.source_db_object._db_node,
                dest=dest._db_node,
                type_=self.relation_type
            )

    def as_set(self):
        """
        Return DB objects that are destinations for self.source_db_object.
        """

        relations = self.all()

        ret = set()

        for rel in relations:
            ret.add(
                self.destination_db_class(**rel.end_node.properties)
            )

        return ret

    def as_list(self):
        relations = self.all()

        ret = []

        for rel in relations:
            ret.append(
                self.destination_db_class(**rel.end_node.properties)
            )

        return ret

    def sources(self, destination_db_object):
        """
        Reverse of self.as_set, i.e. for given destination_db_object,
        return source DB objects.
        """

        relations = self.all_by_dest(destination_db_object)

        ret = set()

        for rel in relations:
            ret.add(
                self.source_db_class(**rel.start_node.properties)
            )

        return ret

    def delete_all_incoming(self,
                            destination_db_object,
                            destination_key=None,
                            tag=None):
        """
        Delete all relations for which destination_db_object is an end node.

        If object is a hash, you can additionally specify the dst_key argument.
        Then only connections that are destinations of dst_key will be deleted.

        Same with tag.
        """
        properties = {}
        if destination_key is not None:
            properties['destination_key'] = destination_key
        if tag is not None:
            properties['tag'] = tag

        db.delete_relations(
            dest=destination_db_object._db_node,
            type_=self.relation_type,
            has_properties=properties or None
        )


def db_related_field(relation_type, destination_db_class):
    class DBRelatedFieldX(DBRelatedField):
        pass

    DBRelatedFieldX.relation_type = relation_type
    DBRelatedFieldX.destination_db_class = destination_db_class

    return DBRelatedFieldX


class DBObjectMeta(type):
    def __new__(cls, name, parents, dct):
        collection = dct.get('_collection')
        if not collection:
            raise NotImplementedError('Collection is required.')

        dct['_meta'] = {}
        dct['_meta']['fields'] = {}
        dct['_meta']['related_to'] = {}

        has_primary = False

        for field_name, field_klass in dct.items():
            if not inspect.isclass(field_klass):
                continue
            if issubclass(field_klass, DBField):
                dct['_meta']['fields'][field_name] = field_klass

                if field_klass.is_primary:
                    if has_primary:
                        raise errors.SolarError('Object cannot have 2 primary fields.')

                    has_primary = True

                    dct['_meta']['primary'] = field_name
            elif issubclass(field_klass, DBRelatedField):
                dct['_meta']['related_to'][field_name] = field_klass

        if not has_primary:
            raise errors.SolarError('Object needs to have a primary field.')

        klass = super(DBObjectMeta, cls).__new__(cls, name, parents, dct)

        # Support for self-references in relations
        for field_name, field_klass in klass._meta['related_to'].items():
            field_klass.source_db_class = klass
            if field_klass.destination_db_class == klass.__name__:
                field_klass.destination_db_class = klass

        return klass


class DBObject(object):
    # Enum from BaseGraphDB.COLLECTIONS
    _collection = None

    def __init__(self, **kwargs):
        wrong_fields = set(kwargs) - set(self._meta['fields'])
        if wrong_fields:
            raise errors.SolarError(
                'Unknown fields {}'.format(wrong_fields)
            )

        self._fields = {}

        for field_name, field_klass in self._meta['fields'].items():
            value = kwargs.get(field_name, field_klass.default_value)

            self._fields[field_name] = field_klass(field_name, value=value)

        self._related_to = {}

        for field_name, field_klass in self._meta['related_to'].items():
            inst = field_klass(field_name, self)
            self._related_to[field_name] = inst

        self._update_values()

    def __eq__(self, inst):
        # NOTE: don't compare related fields
        self._update_fields_values()
        return self._fields == inst._fields

    def __ne__(self, inst):
        return not self.__eq__(inst)

    def __hash__(self):
        return hash(self._db_key)

    def _update_fields_values(self):
        """Copy values from self to self._fields."""

        for field in self._fields.values():
            field.value = getattr(self, field.name)

    def _update_values(self):
        """
        Reverse of _update_fields_values, i.e. copy values from self._fields to
        self."""

        for field in self._fields.values():
            setattr(self, field.name, field.value)

        for field in self._related_to.values():
            setattr(self, field.name, field)

    @property
    def _db_key(self):
        """Key for the DB document (in KV-store).

        You can overwrite this with custom keys."""
        if not self._primary_field.value:
            setattr(self, self._primary_field.name, unicode(uuid.uuid4()))
        self._update_fields_values()
        return self._primary_field.value

    @property
    def _primary_field(self):
        return self._fields[self._meta['primary']]

    @property
    def _db_node(self):
        try:
            return db.get(self._db_key, collection=self._collection)
        except KeyError:
            return

    def validate(self):
        self._update_fields_values()
        for field in self._fields.values():
            if field.schema_in_field is not None:
                field.schema = self._fields[field.schema_in_field].value
            field.validate()

    def to_dict(self):
        self._update_fields_values()
        return {
            f.name: f.value for f in self._fields.values()
        }

    @classmethod
    def load(cls, key):
        r = db.get(key, collection=cls._collection)
        return cls(**r.properties)

    @classmethod
    def load_all(cls):
        rs = db.all(collection=cls._collection)

        return [cls(**r.properties) for r in rs]

    def save(self):
        db.create(
            self._db_key,
            properties=self.to_dict(),
            collection=self._collection
        )

    def delete(self):
        db.delete(
            self._db_key,
            collection=self._collection
        )


class DBResourceInput(DBObject):
    __metaclass__ = DBObjectMeta

    _collection = base.BaseGraphDB.COLLECTIONS.input

    id = db_field(schema='str!', is_primary=True)
    name = db_field(schema='str!')
    schema = db_field()
    value = db_field(schema_in_field='schema')
    is_list = db_field(schema='bool!', default_value=False)
    is_hash = db_field(schema='bool!', default_value=False)

    receivers = db_related_field(base.BaseGraphDB.RELATION_TYPES.input_to_input,
                                 'DBResourceInput')

    @property
    def resource(self):
        return DBResource(
            **db.get_relations(
                dest=self._db_node,
                type_=base.BaseGraphDB.RELATION_TYPES.resource_input
            )[0].start_node.properties
        )

    def delete(self):
        db.delete_relations(
            source=self._db_node,
            type_=base.BaseGraphDB.RELATION_TYPES.input_to_input
        )
        db.delete_relations(
            dest=self._db_node,
            type_=base.BaseGraphDB.RELATION_TYPES.input_to_input
        )
        super(DBResourceInput, self).delete()

    def edges(self):

        out = db.get_relations(
                source=self._db_node,
                type_=base.BaseGraphDB.RELATION_TYPES.input_to_input)
        incoming = db.get_relations(
                dest=self._db_node,
                type_=base.BaseGraphDB.RELATION_TYPES.input_to_input)
        for relation in out + incoming:
            meta = relation.properties
            source = DBResourceInput(**relation.start_node.properties)
            dest = DBResourceInput(**relation.end_node.properties)
            yield source, dest, meta

    def check_other_val(self, other_val=None):
        if not other_val:
            return self
        res = self.resource
        # TODO: needs to be refactored a lot to be more effective.
        # We don't have way of getting single input / value for given resource.
        inps = {i.name: i for i in res.inputs.as_set()}
        correct_input = inps[other_val]
        return correct_input.backtrack_value()

    @cache_me({})
    def backtrack_value_emitter(self, level=None, other_val=None):
        # TODO: this is actually just fetching head element in linked list
        #       so this whole algorithm can be moved to the db backend probably
        # TODO: cycle detection?
        # TODO: write this as a Cypher query? Move to DB?
        if level is not None and other_val is not None:
            raise Exception("Not supported yet")

        if level == 0:
            return self

        def backtrack_func(i):
            if level is None:
                return i.backtrack_value_emitter(other_val=other_val)

            return i.backtrack_value_emitter(level=level - 1, other_val=other_val)

        inputs = self.receivers.sources(self)
        relations = self.receivers.all_by_dest(self)
        source_class = self.receivers.source_db_class

        if not inputs:
            return self.check_other_val(other_val)

            # if lazy_val is None:
            #     return self.value
            # print self.resource.name
            # print [x.name for x in self.resource.inputs.as_set()]
            # _input = next(x for x in self.resource.inputs.as_set() if x.name == lazy_val)
            # return _input.backtrack_value()
            # # return self.value
        if self.is_list:
            if not self.is_hash:
                return [backtrack_func(i) for i in inputs]

            # NOTE: we return a list of values, but we need to group them
            #       hence this dict here
            # NOTE: grouping is done by resource.name by default, but this
            #       can be overwritten by the 'tag' property in relation
            ret = {}

            for r in relations:
                source = source_class(**r.start_node.properties)
                tag = r.properties['tag']
                ret.setdefault(tag, {})
                key = r.properties['destination_key']
                value = backtrack_func(source)

                ret[tag].update({key: value})

            return ret.values()
        elif self.is_hash:
            ret = self.value or {}
            for r in relations:
                source = source_class(
                    **r.start_node.properties
                )
                # NOTE: hard way to do this, what if there are more relations
                #       and some of them do have destination_key while others
                #       don't?
                if 'destination_key' not in r.properties:
                    return backtrack_func(source)
                key = r.properties['destination_key']
                ret[key] = backtrack_func(source)
            return ret

        return backtrack_func(inputs.pop())

    def parse_backtracked_value(self, v):
        if isinstance(v, DBResourceInput):
            return v.value

        if isinstance(v, list):
            return [self.parse_backtracked_value(vv) for vv in v]

        if isinstance(v, dict):
            return {
                k: self.parse_backtracked_value(vv) for k, vv in v.items()
            }

        return v

    def backtrack_value(self, other_val=None):
        return self.parse_backtracked_value(self.backtrack_value_emitter(other_val=other_val))


class DBEvent(DBObject):

    __metaclass__ = DBObjectMeta

    _collection = base.BaseGraphDB.COLLECTIONS.events

    id = db_field(is_primary=True)
    parent = db_field(schema='str!')
    parent_action = db_field(schema='str!')
    etype = db_field('str!')
    state = db_field('str')
    child = db_field('str')
    child_action = db_field('str')

    def delete(self):
        db.delete_relations(
            dest=self._db_node,
            type_=base.BaseGraphDB.RELATION_TYPES.resource_event
        )
        super(DBEvent, self).delete()


class DBResourceEvents(DBObject):

    __metaclass__ = DBObjectMeta

    _collection = base.BaseGraphDB.COLLECTIONS.resource_events

    id = db_field(schema='str!', is_primary=True)
    events = db_related_field(base.BaseGraphDB.RELATION_TYPES.resource_event,
                              DBEvent)

    @classmethod
    def get_or_create(cls, name):
        r = db.get_or_create(
            name,
            properties={'id': name},
            collection=cls._collection)
        return cls(**r.properties)


class DBCommitedState(DBObject):

    __metaclass__ = DBObjectMeta

    _collection = base.BaseGraphDB.COLLECTIONS.state_data

    id = db_field(schema='str!', is_primary=True)
    inputs = db_field(schema={}, default_value={})
    connections = db_field(schema=[], default_value=[])
    base_path = db_field(schema='str')
    tags = db_field(schema=[], default_value=[])
    state = db_field(schema='str', default_value='removed')

    @classmethod
    def get_or_create(cls, name):
        r = db.get_or_create(
            name,
            properties={'id': name},
            collection=cls._collection)
        return cls(**r.properties)


class DBResource(DBObject):
    __metaclass__ = DBObjectMeta

    _collection = base.BaseGraphDB.COLLECTIONS.resource

    id = db_field(schema='str', is_primary=True)
    name = db_field(schema='str!')
    actions_path = db_field(schema='str')
    base_name = db_field(schema='str')
    base_path = db_field(schema='str')
    handler = db_field(schema='str')  # one of: {'ansible_playbook', 'ansible_template', 'puppet', etc}
    puppet_module = db_field(schema='str')
    version = db_field(schema='str')
    tags = db_field(schema=[], default_value=[])
    meta_inputs = db_field(schema={}, default_value={})
    state = db_field(schema='str')

    inputs = db_related_field(base.BaseGraphDB.RELATION_TYPES.resource_input,
                              DBResourceInput)

    def add_input(self, name, schema, value):
        # NOTE: Inputs need to have uuid added because there can be many
        #       inputs with the same name
        uid = '{}-{}'.format(name, uuid.uuid4())
        input = DBResourceInput(id=uid,
                                name=name,
                                schema=schema,
                                value=value,
                                is_list=isinstance(schema, list),
                                is_hash=isinstance(schema, dict) or (isinstance(schema, list) and len(schema) > 0 and isinstance(schema[0], dict)))
        input.save()

        self.inputs.add(input)

    def add_event(self, action, state, etype, child, child_action):
        event = DBEvent(
            parent=self.name,
            parent_action=action,
            state=state,
            etype=etype,
            child=child,
            child_action=child_action
            )
        event.save()
        self.events.add(event)

    def delete(self):
        for input in self.inputs.as_set():
            self.inputs.remove(input)
            input.delete()
        super(DBResource, self).delete()

    def graph(self):
        mdg = networkx.MultiDiGraph()
        for input in self.inputs.as_list():
            mdg.add_edges_from(input.edges())
        return mdg

    def add_tags(self, *tags):
        self.tags = list(set(self.tags) | set(tags))
        self.save()

    def remove_tags(self, *tags):
        self.tags = list(set(self.tags) - set(tags))
        self.save()

# TODO: remove this
if __name__ == '__main__':
    r = DBResource(name=1)
    r.validate()
