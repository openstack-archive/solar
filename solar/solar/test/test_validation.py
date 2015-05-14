import unittest

import base

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


if __name__ == '__main__':
    unittest.main()
