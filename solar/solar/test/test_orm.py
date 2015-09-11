import unittest

from solar.core import resource
from solar import errors
from solar.interfaces import orm
from solar.interfaces.db import base


class TestORM(unittest.TestCase):
    def test_no_collection_defined(self):
        with self.assertRaisesRegexp(NotImplementedError, 'Collection is required.'):
            class TestDBObject(orm.DBObject):
                __metaclass__ = orm.DBObjectMeta

    def test_has_primary(self):
        with self.assertRaisesRegexp(errors.SolarError, 'Object needs to have a primary field.'):
            class TestDBObject(orm.DBObject):
                _collection = base.BaseGraphDB.COLLECTIONS.resource
                __metaclass__ = orm.DBObjectMeta

                test1 = orm.db_field('str')

    def test_no_multiple_primaries(self):
        with self.assertRaisesRegexp(errors.SolarError, 'Object cannot have 2 primary fields.'):
            class TestDBObject(orm.DBObject):
                _collection = base.BaseGraphDB.COLLECTIONS.resource
                __metaclass__ = orm.DBObjectMeta

                test1 = orm.db_field('str', is_primary=True)
                test2 = orm.db_field('str', is_primary=True)

    def test_primary_field(self):
        class TestDBObject(orm.DBObject):
            _collection = base.BaseGraphDB.COLLECTIONS.resource
            __metaclass__ = orm.DBObjectMeta

            test1 = orm.db_field('str', is_primary=True)

        t = TestDBObject(test1='abc')

        self.assertEqual('test1', t._primary_field.name)
        self.assertEqual('abc', t._db_key)

        t = TestDBObject()
        self.assertIsNotNone(t._db_key)
        self.assertIsNotNone(t.test1)

    def test_field_validation(self):
        class TestDBObject(orm.DBObject):
            _collection = base.BaseGraphDB.COLLECTIONS.resource
            __metaclass__ = orm.DBObjectMeta

            id = orm.db_field('str', is_primary=True)

        t = TestDBObject(id=1)

        with self.assertRaises(errors.ValidationError):
            t.validate()

    def test_wrong_fields(self):
        class TestDBObject(orm.DBObject):
            _collection = base.BaseGraphDB.COLLECTIONS.resource
            __metaclass__ = orm.DBObjectMeta

            id = orm.db_field('str', is_primary=True)

        with self.assertRaisesRegexp(errors.SolarError, 'Unknown fields .*iid'):
            TestDBObject(iid=1)


class TestResourceORM(unittest.TestCase):
    def test_save(self):
        r = orm.DBResource(name='test1', base_path='x')

        r.save()

        rr = resource.load(r.name)
