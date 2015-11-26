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

from solar.test import base

from solar import errors
from solar.core import validation as sv


class TestInputValidation(base.BaseResourceTest):

    def test_input_str_type(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  value:
    schema: str
    value:
  value-required:
    schema: str!
    value:
        """)

        r = self.create_resource(
            'r1', sample_meta_dir, {'value': 'x', 'value-required': 'y'}
        )
        es = sv.validate_resource(r)
        self.assertEqual(es, {})

        r = self.create_resource(
            'r2', sample_meta_dir, {'value': 1, 'value-required': 'y'}
        )
        es = sv.validate_resource(r)
        self.assertIn('value', es)
        self.assertIn('1 is not valid', es['value'][0])

        r = self.create_resource(
            'r3', sample_meta_dir, {'value': ''}
        )
        es = sv.validate_resource(r)
        self.assertIn('value-required', es)
        self.assertIn("None is not of type 'string'", es['value-required'][0])

        r = self.create_resource(
            'r4', sample_meta_dir, {'value': None, 'value-required': 'y'}
        )

    def test_input_int_type(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  value:
    schema: int
    value:
  value-required:
    schema: int!
    value:
        """)

        r = self.create_resource(
            'r1', sample_meta_dir, {'value': 1, 'value-required': 2}
        )
        es = sv.validate_resource(r)
        self.assertEqual(es, {})

        r = self.create_resource(
            'r2', sample_meta_dir, {'value': 'x', 'value-required': 2}
        )
        es = sv.validate_resource(r)
        self.assertIn('value', es)
        self.assertIn("'x' is not valid", es['value'][0])

        r = self.create_resource(
            'r3', sample_meta_dir, {'value': 1}
        )
        es = sv.validate_resource(r)
        self.assertIn('value-required', es)
        self.assertIn("None is not of type 'number'", es['value-required'][0])

        r = self.create_resource(
            'r4', sample_meta_dir, {'value': None, 'value-required': 2}
        )

    def test_input_dict_type(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  values:
    schema: {a: int!, b: int}
    value: {}
        """)

        r = self.create_resource(
            'r', sample_meta_dir, {'values': {'a': 1, 'b': 2}}
        )
        es = sv.validate_resource(r)
        self.assertEqual(es, {})

        r.update({'values': None})
        es = sv.validate_resource(r)
        self.assertListEqual(es.keys(), ['values'])

        r.update({'values': {'a': 1, 'c': 3}})
        es = sv.validate_resource(r)
        self.assertEqual(es, {})

        r = self.create_resource(
            'r1', sample_meta_dir, {'values': {'b': 2}}
        )
        es = sv.validate_resource(r)
        self.assertIn('values', es)
        self.assertIn("'a' is a required property", es['values'][0])

    def test_complex_input(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  values:
    schema: {l: [{a: int}]}
    value: {l: [{a: 1}]}
        """)

        r = self.create_resource(
            'r', sample_meta_dir, {
                'values': {
                    'l': [{'a': 1}],
                }
            }
        )
        errors = sv.validate_resource(r)
        self.assertEqual(errors, {})

        r.update({
            'values': {
                'l': [{'a': 'x'}],
            }
        })
        errors = sv.validate_resource(r)
        self.assertListEqual(errors.keys(), ['values'])

        r.update({'values': {'l': [{'a': 1, 'c': 3}]}})
        errors = sv.validate_resource(r)
        self.assertEqual(errors, {})

    def test_more_complex_input(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  values:
    schema: {l: [{a: int}], d: {x: [int]}}
    value: {l: [{a: 1}], d: {x: [1, 2]}}
        """)

        r = self.create_resource(
            'r', sample_meta_dir, {
                'values': {
                    'l': [{'a': 1}],
                    'd': {'x': [1, 2]}
                }
            }
        )
        errors = sv.validate_resource(r)
        self.assertEqual(errors, {})

        r.update({
            'values': {
                'l': [{'a': 1}],
                'd': []
            }
        })
        errors = sv.validate_resource(r)
        self.assertListEqual(errors.keys(), ['values'])

        r.update({'values': {'a': 1, 'c': 3}})
        errors = sv.validate_resource(r)
        self.assertEqual(errors, {})
