import unittest

import base

from solar.core import signals as xs


class TestResource(base.BaseResourceTest):
    def test_resource_args(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  value:
    schema: int
    value: 0
        """)

        sample1 = self.create_resource(
            'sample1', sample_meta_dir, {'value': 1}
        )
        self.assertEqual(sample1.args['value'].value, 1)

        # test default value
        sample2 = self.create_resource('sample2', sample_meta_dir, {})
        self.assertEqual(sample2.args['value'].value, 0)


if __name__ == '__main__':
    unittest.main()
