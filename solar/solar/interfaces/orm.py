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
import uuid

from solar import errors
from solar.core import validation
from solar.interfaces.db import base
from solar.interfaces.db import get_db


db = get_db()


class DBField(object):
    is_primary = False
    schema = None
    schema_in_field = None
    default_value = None

    def __init__(self, name, value=None):
        self.name = name
        self.value = value or self.default_value

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
    destination_db_class = None
    relation_type = None

    def __init__(self, name, source_db_object):
        self.name = name
        self.source_db_object = source_db_object

    def add(self, *destination_db_objects):
        for dest in destination_db_objects:
            db.get_or_create_relation(
                self.source_db_object._db_node,
                dest._db_node,
                properties={},
                type_=self.relation_type
            )

    def remove(self, *destination_db_objects):
        for dest in destination_db_objects:
            db.delete_relations(
                source=self.source_db_object._db_node,
                dest=dest._db_node,
                type_=self.relation_type
            )

    @property
    def value(self):
        source_db_node = self.source_db_object._db_node

        if source_db_node is None:
            return set()

        relations = db.get_relations(source=source_db_node,
                                     type_=self.relation_type)

        ret = set()

        for rel in relations:
            ret.add(
                self.destination_db_class(**rel.end_node.properties)
            )

        return ret


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
                field_klass._parent_db_class = cls
                dct['_meta']['related_to'][field_name] = field_klass

        if not has_primary:
            raise errors.SolarError('Object needs to have a primary field.')

        return super(DBObjectMeta, cls).__new__(cls, name, parents, dct)


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

    def save(self):
        db.create(
            self._db_key,
            properties=self.to_dict(),
            collection=self._collection
        )


class DBResourceInput(DBObject):
    __metaclass__ = DBObjectMeta

    _collection = base.BaseGraphDB.COLLECTIONS.input

    id = db_field(schema='str!', is_primary=True)
    name = db_field(schema='str!')
    schema = db_field()
    value = db_field(schema_in_field='schema')


class DBResource(DBObject):
    __metaclass__ = DBObjectMeta

    _collection = base.BaseGraphDB.COLLECTIONS.resource

    id = db_field(schema='str', is_primary=True)
    name = db_field(schema='str!')
    actions_path = db_field(schema='str')
    base_name = db_field(schema='str')
    base_path = db_field(schema='str')
    handler = db_field(schema='str')  # one of: {'ansible_playbook', 'ansible_template', 'puppet', etc}
    version = db_field(schema='str')
    tags = db_field(schema=[], default_value=[])

    inputs = db_related_field(base.BaseGraphDB.RELATION_TYPES.resource_input,
                              DBResourceInput)

    def add_input(self, name, schema, value):
        # NOTE: Inputs need to have uuid added because there can be many
        #       inputs with the same name
        uid = '{}-{}'.format(name, uuid.uuid4())
        input = DBResourceInput(id=uid, name=name, schema=schema, value=value)
        input.validate()
        input.save()

        self.inputs.add(input)


# TODO: remove this
if __name__ == '__main__':
    r = DBResource(name=1)
    r.validate()
