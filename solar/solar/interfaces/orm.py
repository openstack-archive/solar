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
    default_value = None

    def __init__(self, name, value=None):
        self.name = name
        self.value = value or self.default_value

    def validate(self):
        es = validation.validate_input(self.value, schema=self.schema)
        if es:
            raise errors.ValidationError('"{}": {}'.format(self.name, es[0]))


def db_field(schema, default_value=None, is_primary=False):
    """Definition for the DB field.

    schema - simple schema according to the one in solar.core.validation
    is_primary - only one field in db object can be primary. This key is used
        for creating key in the DB
    """

    class DBFieldX(DBField):
        pass

    DBFieldX.is_primary = is_primary
    DBFieldX.schema = schema
    if default_value is not None:
        DBFieldX.default_value = default_value

    return DBFieldX


class DBObjectMeta(type):
    def __new__(cls, name, parents, dct):
        collection = dct.get('_collection')
        if not collection:
            raise NotImplementedError('Collection is required.')

        dct['_meta'] = {}
        dct['_meta']['fields'] = {}

        has_primary = False

        for field_name, field_klass in dct.items():
            if not inspect.isclass(field_klass):
                continue
            if not issubclass(field_klass, DBField):
                continue

            dct['_meta']['fields'][field_name] = field_klass

            if field_klass.is_primary:
                if has_primary:
                    raise errors.SolarError('Object cannot have 2 primary fields.')

                has_primary = True

                dct['_meta']['primary'] = field_name

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
            value = kwargs.get(field_name)

            self._fields[field_name] = field_klass(field_name, value=value)
            setattr(self, field_name, value)

    def _update_values(self):
        """Copy values from self to self._fields."""

        for field in self._fields.values():
            field.value = getattr(self, field.name)

    @property
    def _db_key(self):
        """Key for the DB document (in KV-store).

        You can overwrite this with custom keys."""
        if not self._primary_field.value:
            setattr(self, self._primary_field.name, unicode(uuid.uuid4()))
        self._update_values()
        return self._primary_field.value

    @property
    def _primary_field(self):
        return self._fields[self._meta['primary']]

    def validate(self):
        self._update_values()
        for field in self._fields.values():
            field.validate()

    def to_dict(self):
        self._update_values()
        return {
            f.name: f.value for f in self._fields.values()
        }

    def save(self):
        db.create(
            self._db_key,
            self.to_dict(),
            collection=self._collection
        )


class DBResource(DBObject):
    __metaclass__ = DBObjectMeta

    _collection = base.BaseGraphDB.COLLECTIONS.resource

    name = db_field('str!', is_primary=True)
    actions_path = db_field('str')
    base_name = db_field('str')
    base_path = db_field('str')
    handler = db_field('str')  # one of: {'ansible_playbook', 'ansible_template', 'puppet', etc}
    id = db_field('str')
    version = db_field('str')


# TODO: remove this
if __name__ == '__main__':
    r = DBResource(name=1)
    r.validate()
