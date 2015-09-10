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

import unittest

from solar.test import base

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
        errors = sv.validate_resource(r)
        self.assertEqual(errors, {})

        r = self.create_resource(
            'r2', sample_meta_dir, {'value': 1, 'value-required': 'y'}
        )
        errors = sv.validate_resource(r)
        self.assertListEqual(errors.keys(), ['value'])

        r = self.create_resource(
            'r3', sample_meta_dir, {'value': ''}
        )
        errors = sv.validate_resource(r)
        self.assertListEqual(errors.keys(), ['value-required'])

        r = self.create_resource(
            'r4', sample_meta_dir, {'value': None, 'value-required': 'y'}
        )
        errors = sv.validate_resource(r)
        self.assertEqual(errors, {})

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
        errors = sv.validate_resource(r)
        self.assertEqual(errors, {})

        r = self.create_resource(
            'r2', sample_meta_dir, {'value': 'x', 'value-required': 2}
        )
        errors = sv.validate_resource(r)
        self.assertListEqual(errors.keys(), ['value'])

        r = self.create_resource(
            'r3', sample_meta_dir, {'value': 1}
        )
        errors = sv.validate_resource(r)
        self.assertListEqual(errors.keys(), ['value-required'])

        r = self.create_resource(
            'r4', sample_meta_dir, {'value': None, 'value-required': 2}
        )
        errors = sv.validate_resource(r)
        self.assertEqual(errors, {})

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
        errors = sv.validate_resource(r)
        self.assertEqual(errors, {})

        r.update({'values': None})
        errors = sv.validate_resource(r)
        self.assertListEqual(errors.keys(), ['values'])

        r.update({'values': {'a': 1, 'c': 3}})
        errors = sv.validate_resource(r)
        self.assertEqual(errors, {})

        r = self.create_resource(
            'r1', sample_meta_dir, {'values': {'b': 2}}
        )
        errors = sv.validate_resource(r)
        self.assertListEqual(errors.keys(), ['values'])

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

if __name__ == '__main__':
    unittest.main()
