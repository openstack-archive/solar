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

from .base import BaseResourceTest

from solar.core import resource
from solar.core import signals
from solar import errors
from solar.interfaces import orm
from solar.interfaces.db import base


class TestORM(BaseResourceTest):
    def test_no_collection_defined(self):
        with self.assertRaisesRegexp(NotImplementedError, 'Collection is required.'):
            class TestDBObject(orm.DBObject):
                __metaclass__ = orm.DBObjectMeta

    def test_has_primary(self):
        with self.assertRaisesRegexp(errors.SolarError, 'Object needs to have a primary field.'):
            class TestDBObject(orm.DBObject):
                _collection = base.BaseGraphDB.COLLECTIONS.resource
                __metaclass__ = orm.DBObjectMeta

                test1 = orm.db_field(schema='str')

    def test_no_multiple_primaries(self):
        with self.assertRaisesRegexp(errors.SolarError, 'Object cannot have 2 primary fields.'):
            class TestDBObject(orm.DBObject):
                _collection = base.BaseGraphDB.COLLECTIONS.resource
                __metaclass__ = orm.DBObjectMeta

                test1 = orm.db_field(schema='str', is_primary=True)
                test2 = orm.db_field(schema='str', is_primary=True)

    def test_primary_field(self):
        class TestDBObject(orm.DBObject):
            _collection = base.BaseGraphDB.COLLECTIONS.resource
            __metaclass__ = orm.DBObjectMeta

            test1 = orm.db_field(schema='str', is_primary=True)

        t = TestDBObject(test1='abc')

        self.assertEqual('test1', t._primary_field.name)
        self.assertEqual('abc', t._db_key)

        t = TestDBObject()
        self.assertIsNotNone(t._db_key)
        self.assertIsNotNone(t.test1)

    def test_default_value(self):
        class TestDBObject(orm.DBObject):
            _collection = base.BaseGraphDB.COLLECTIONS.resource
            __metaclass__ = orm.DBObjectMeta

            test1 = orm.db_field(schema='str',
                                 is_primary=True,
                                 default_value='1')

        t = TestDBObject()

        self.assertEqual('1', t.test1)

    def test_field_validation(self):
        class TestDBObject(orm.DBObject):
            _collection = base.BaseGraphDB.COLLECTIONS.resource
            __metaclass__ = orm.DBObjectMeta

            id = orm.db_field(schema='str', is_primary=True)

        t = TestDBObject(id=1)

        with self.assertRaises(errors.ValidationError):
            t.validate()

        t = TestDBObject(id='1')
        t.validate()

    def test_dynamic_schema_validation(self):
        class TestDBObject(orm.DBObject):
            _collection = base.BaseGraphDB.COLLECTIONS.resource
            __metaclass__ = orm.DBObjectMeta

            id = orm.db_field(schema='str', is_primary=True)
            schema = orm.db_field()
            value = orm.db_field(schema_in_field='schema')

        t = TestDBObject(id='1', schema='str', value=1)

        with self.assertRaises(errors.ValidationError):
            t.validate()

        self.assertEqual(t._fields['value'].schema, t._fields['schema'].value)

        t = TestDBObject(id='1', schema='int', value=1)
        t.validate()
        self.assertEqual(t._fields['value'].schema, t._fields['schema'].value)

    def test_unknown_fields(self):
        class TestDBObject(orm.DBObject):
            _collection = base.BaseGraphDB.COLLECTIONS.resource
            __metaclass__ = orm.DBObjectMeta

            id = orm.db_field(schema='str', is_primary=True)

        with self.assertRaisesRegexp(errors.SolarError, 'Unknown fields .*iid'):
            TestDBObject(iid=1)

    def test_equality(self):
        class TestDBObject(orm.DBObject):
            _collection = base.BaseGraphDB.COLLECTIONS.resource
            __metaclass__ = orm.DBObjectMeta

            id = orm.db_field(schema='str', is_primary=True)
            test = orm.db_field(schema='str')

        t1 = TestDBObject(id='1', test='test')

        t2 = TestDBObject(id='2', test='test')
        self.assertNotEqual(t1, t2)

        t2 = TestDBObject(id='1', test='test2')
        self.assertNotEqual(t1, t2)

        t2 = TestDBObject(id='1', test='test')
        self.assertEqual(t1, t2)


class TestORMRelation(BaseResourceTest):
    def test_children_value(self):
        class TestDBRelatedObject(orm.DBObject):
            _collection = base.BaseGraphDB.COLLECTIONS.input
            __metaclass__ = orm.DBObjectMeta

            id = orm.db_field(schema='str', is_primary=True)

        class TestDBObject(orm.DBObject):
            _collection = base.BaseGraphDB.COLLECTIONS.resource
            __metaclass__ = orm.DBObjectMeta

            id = orm.db_field(schema='str', is_primary=True)
            related = orm.db_related_field(
                base.BaseGraphDB.RELATION_TYPES.resource_input,
                TestDBRelatedObject
            )

        r1 = TestDBRelatedObject(id='1')
        r1.save()
        r2 = TestDBRelatedObject(id='2')
        r2.save()

        o = TestDBObject(id='a')
        o.save()

        self.assertSetEqual(o.related.as_set(), set())

        o.related.add(r1)
        self.assertSetEqual(o.related.as_set(), {r1})

        o.related.add(r2)
        self.assertSetEqual(o.related.as_set(), {r1, r2})

        o.related.remove(r2)
        self.assertSetEqual(o.related.as_set(), {r1})

        o.related.add(r2)
        self.assertSetEqual(o.related.as_set(), {r1, r2})

        o.related.remove(r1, r2)
        self.assertSetEqual(o.related.as_set(), set())

        o.related.add(r1, r2)
        self.assertSetEqual(o.related.as_set(), {r1, r2})

        with self.assertRaisesRegexp(errors.SolarError, '.*incompatible type.*'):
            o.related.add(o)

    def test_relation_to_self(self):
        class TestDBObject(orm.DBObject):
            _collection = base.BaseGraphDB.COLLECTIONS.input
            __metaclass__ = orm.DBObjectMeta

            id = orm.db_field(schema='str', is_primary=True)
            related = orm.db_related_field(
                base.BaseGraphDB.RELATION_TYPES.input_to_input,
                'TestDBObject'
            )

        o1 = TestDBObject(id='1')
        o1.save()
        o2 = TestDBObject(id='2')
        o2.save()
        o3 = TestDBObject(id='2')
        o3.save()

        o1.related.add(o2)
        o2.related.add(o3)

        self.assertEqual(o1.related.as_set(), {o2})
        self.assertEqual(o2.related.as_set(), {o3})


class TestResourceORM(BaseResourceTest):
    def test_save(self):
        r = orm.DBResource(id='test1', name='test1', base_path='x')
        r.save()

        rr = resource.load(r.id)

        self.assertEqual(r, rr.db_obj)

    def test_add_input(self):
        r = orm.DBResource(id='test1', name='test1', base_path='x')
        r.save()

        r.add_input('ip', 'str!', '10.0.0.2')

        self.assertEqual(len(r.inputs.as_set()), 1)


class TestResourceInputORM(BaseResourceTest):
    def test_backtrack_simple(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  value:
    schema: str!
    value:
        """)

        sample1 = self.create_resource(
            'sample1', sample_meta_dir, {'value': 'x'}
        )
        sample2 = self.create_resource(
            'sample2', sample_meta_dir, {'value': 'y'}
        )
        sample3 = self.create_resource(
            'sample3', sample_meta_dir, {'value': 'z'}
        )
        vi = sample2.resource_inputs()['value']
        self.assertEqual(vi.backtrack_value_emitter(), vi)

        # sample1 -> sample2
        signals.connect(sample1, sample2)
        self.assertEqual(vi.backtrack_value_emitter(),
                         sample1.resource_inputs()['value'])

        # sample3 -> sample1 -> sample2
        signals.connect(sample3, sample1)
        self.assertEqual(vi.backtrack_value_emitter(),
                         sample3.resource_inputs()['value'])

        # sample2 disconnected
        signals.disconnect(sample1, sample2)
        self.assertEqual(vi.backtrack_value_emitter(), vi)

    def test_backtrack_list(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  value:
    schema: str!
    value:
        """)
        sample_list_meta_dir = self.make_resource_meta("""
id: sample_list
handler: ansible
version: 1.0.0
input:
  values:
    schema: [str!]
    value:
        """)

        sample_list = self.create_resource(
            'sample_list', sample_list_meta_dir
        )
        vi = sample_list.resource_inputs()['values']
        sample1 = self.create_resource(
            'sample1', sample_meta_dir, {'value': 'x'}
        )
        sample2 = self.create_resource(
            'sample2', sample_meta_dir, {'value': 'y'}
        )
        sample3 = self.create_resource(
            'sample3', sample_meta_dir, {'value': 'z'}
        )
        self.assertEqual(vi.backtrack_value_emitter(), vi)

        # [sample1] -> sample_list
        signals.connect(sample1, sample_list, {'value': 'values'})
        self.assertEqual(vi.backtrack_value_emitter(),
                         [sample1.resource_inputs()['value']])

        # [sample3, sample1] -> sample_list
        signals.connect(sample3, sample_list, {'value': 'values'})
        self.assertSetEqual(set(vi.backtrack_value_emitter()),
                            set([sample1.resource_inputs()['value'],
                                 sample3.resource_inputs()['value']]))

        # sample2 disconnected
        signals.disconnect(sample1, sample_list)
        self.assertEqual(vi.backtrack_value_emitter(),
                         [sample3.resource_inputs()['value']])

    def test_backtrack_dict(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  value:
    schema: str!
    value:
        """)
        sample_dict_meta_dir = self.make_resource_meta("""
id: sample_dict
handler: ansible
version: 1.0.0
input:
  value:
    schema: {a: str!}
    value:
        """)

        sample_dict = self.create_resource(
            'sample_dict', sample_dict_meta_dir
        )
        vi = sample_dict.resource_inputs()['value']
        sample1 = self.create_resource(
            'sample1', sample_meta_dir, {'value': 'x'}
        )
        sample2 = self.create_resource(
            'sample2', sample_meta_dir, {'value': 'z'}
        )
        self.assertEqual(vi.backtrack_value_emitter(), vi)

        # {a: sample1} -> sample_dict
        signals.connect(sample1, sample_dict, {'value': 'value:a'})
        self.assertDictEqual(vi.backtrack_value_emitter(),
                             {'a': sample1.resource_inputs()['value']})

        # {a: sample2} -> sample_dict
        signals.connect(sample2, sample_dict, {'value': 'value:a'})
        self.assertDictEqual(vi.backtrack_value_emitter(),
                             {'a': sample2.resource_inputs()['value']})

        # sample2 disconnected
        signals.disconnect(sample2, sample_dict)
        self.assertEqual(vi.backtrack_value_emitter(), vi)

    def test_backtrack_dict_list(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  value:
    schema: str!
    value:
        """)
        sample_dict_list_meta_dir = self.make_resource_meta("""
id: sample_dict_list
handler: ansible
version: 1.0.0
input:
  value:
    schema: [{a: str!}]
    value:
        """)

        sample_dict_list = self.create_resource(
            'sample_dict', sample_dict_list_meta_dir
        )
        vi = sample_dict_list.resource_inputs()['value']
        sample1 = self.create_resource(
            'sample1', sample_meta_dir, {'value': 'x'}
        )
        sample2 = self.create_resource(
            'sample2', sample_meta_dir, {'value': 'y'}
        )
        sample3 = self.create_resource(
            'sample3', sample_meta_dir, {'value': 'z'}
        )
        self.assertEqual(vi.backtrack_value_emitter(), vi)

        # [{a: sample1}] -> sample_dict_list
        signals.connect(sample1, sample_dict_list, {'value': 'value:a'})
        self.assertListEqual(vi.backtrack_value_emitter(),
                             [{'a': sample1.resource_inputs()['value']}])

        # [{a: sample1}, {a: sample3}] -> sample_dict_list
        signals.connect(sample3, sample_dict_list, {'value': 'value:a'})
        self.assertItemsEqual(vi.backtrack_value_emitter(),
                              [{'a': sample1.resource_inputs()['value']},
                               {'a': sample3.resource_inputs()['value']}])

        # [{a: sample1}, {a: sample2}] -> sample_dict_list
        signals.connect(sample2, sample_dict_list, {'value': 'value:a|sample3'})
        self.assertItemsEqual(vi.backtrack_value_emitter(),
                              [{'a': sample1.resource_inputs()['value']},
                               {'a': sample2.resource_inputs()['value']}])

        # sample2 disconnected
        signals.disconnect(sample2, sample_dict_list)
        self.assertEqual(vi.backtrack_value_emitter(), [vi])
