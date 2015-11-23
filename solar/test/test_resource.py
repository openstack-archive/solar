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

import base

from solar.core import resource
from solar.core import signals


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
        self.assertEqual(sample1.args['value'], 1)

        # test default value
        sample2 = self.create_resource('sample2', sample_meta_dir, {})
        self.assertEqual(sample2.args['value'], 0)

    def test_connections_recreated_after_load(self):
        """
        Create resource in some process. Then in other process load it.
        All connections should remain the same.
        """
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  value:
    schema: int
    value: 0
        """)

        def creating_process():
            sample1 = self.create_resource(
                'sample1', sample_meta_dir, {'value': 1}
            )
            sample2 = self.create_resource(
                'sample2', sample_meta_dir,
            )
            signals.connect(sample1, sample2)
            self.assertEqual(sample1.args['value'], sample2.args['value'])

        creating_process()

        signals.CLIENTS = {}

        sample1 = resource.load('sample1')
        sample2 = resource.load('sample2')

        sample1.update({'value': 2})
        self.assertEqual(sample1.args['value'], sample2.args['value'])

    def test_load(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  value:
    schema: int
    value: 0
        """)

        sample = self.create_resource(
            'sample', sample_meta_dir, {'value': 1}
        )

        sample_l = resource.load('sample')

        self.assertDictEqual(sample.args, sample_l.args)
        self.assertListEqual(list(sample.tags), list(sample_l.tags))

    def test_removal(self):
        """Test that connection removed with resource."""
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
        sample2 = self.create_resource(
            'sample2', sample_meta_dir, {}
        )
        signals.connect(sample1, sample2)
        self.assertEqual(sample1.args['value'], sample2.args['value'])

        sample1 = resource.load('sample1')
        sample2 = resource.load('sample2')
        sample1.delete()
        self.assertEqual(sample2.args['value'], 0)
