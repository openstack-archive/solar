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

from solar.core import signals as xs

import pytest


class TestBaseInput(base.BaseResourceTest):

    def test_no_self_connection(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  value:
    schema: str!
    value:
        """)

        sample = self.create_resource(
            'sample', sample_meta_dir, {'value': 'x'}
        )

        with self.assertRaisesRegexp(
                Exception,
                'Trying to connect value-.* to itself'):
            xs.connect(sample, sample, {'value'})

    def test_input_dict_type(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  values:
    schema: {a: int, b: int}
    value: {}
        """)

        sample1 = self.create_resource(
            'sample1', sample_meta_dir, {'values': {'a': 1, 'b': 2}}
        )
        sample2 = self.create_resource(
            'sample2', sample_meta_dir
        )
        xs.connect(sample1, sample2)
        self.assertEqual(
            sample1.args['values'],
            sample2.args['values']
        )

        # Check update
        sample1.update({'values': {'a': 2}})
        self.assertEqual(
            sample1.args['values'],
            {'a': 2}
        )
        self.assertEqual(
            sample1.args['values'],
            sample2.args['values'],
        )

        # Check disconnect
        # TODO: should sample2.value be reverted to original value?
        sample1.disconnect(sample2)
        sample1.update({'values': {'a': 3}})
        self.assertEqual(
            sample1.args['values'],
            {'a': 3}
        )
        # self.assertEqual(
        #    sample2.args['values'],
        #    {'a': 2}
        #)
        #self.assertEqual(sample2.args['values'].emitter, None)

    def test_multiple_resource_disjoint_connect(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  ip:
    schema: str
    value:
  port:
    schema: int
    value:
        """)
        sample_ip_meta_dir = self.make_resource_meta("""
id: sample-ip
handler: ansible
version: 1.0.0
input:
  ip:
    schema: str
    value:
        """)
        sample_port_meta_dir = self.make_resource_meta("""
id: sample-port
handler: ansible
version: 1.0.0
input:
  port:
    schema: int
    value:
        """)

        sample = self.create_resource(
            'sample', sample_meta_dir, {'ip': None, 'port': None}
        )
        sample_ip = self.create_resource(
            'sample-ip', sample_ip_meta_dir, {'ip': '10.0.0.1'}
        )
        sample_port = self.create_resource(
            'sample-port', sample_port_meta_dir, {'port': 8000}
        )
        self.assertNotEqual(
            sample.resource_inputs()['ip'],
            sample_ip.resource_inputs()['ip'],
        )
        xs.connect(sample_ip, sample)
        xs.connect(sample_port, sample)
        self.assertEqual(sample.args['ip'], sample_ip.args['ip'])
        self.assertEqual(sample.args['port'], sample_port.args['port'])
        # self.assertEqual(
        #    sample.args['ip'].emitter,
        #    sample_ip.args['ip']
        #)
        # self.assertEqual(
        #    sample.args['port'].emitter,
        #    sample_port.args['port']
        #)

    def test_simple_observer_unsubscription(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  ip:
    schema: str
    value:
        """)

        sample = self.create_resource(
            'sample', sample_meta_dir, {'ip': None}
        )
        sample1 = self.create_resource(
            'sample1', sample_meta_dir, {'ip': '10.0.0.1'}
        )
        sample2 = self.create_resource(
            'sample2', sample_meta_dir, {'ip': '10.0.0.2'}
        )

        xs.connect(sample1, sample)
        self.assertEqual(sample1.args['ip'], sample.args['ip'])
        #self.assertEqual(len(list(sample1.args['ip'].receivers)), 1)
        # self.assertEqual(
        #    sample.args['ip'].emitter,
        #    sample1.args['ip']
        #)

        xs.connect(sample2, sample)
        self.assertEqual(sample2.args['ip'], sample.args['ip'])
        # sample should be unsubscribed from sample1 and subscribed to sample2
        #self.assertEqual(len(list(sample1.args['ip'].receivers)), 0)
        #self.assertEqual(sample.args['ip'].emitter, sample2.args['ip'])

        sample2.update({'ip': '10.0.0.3'})
        self.assertEqual(sample2.args['ip'], sample.args['ip'])

    @pytest.mark.xfail(reason="No cycle detection in new_db")
    def test_circular_connection_prevention(self):
        # TODO: more complex cases
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  ip:
    schema: str
    value:
        """)

        sample1 = self.create_resource(
            'sample1', sample_meta_dir, {'ip': '10.0.0.1'}
        )
        sample2 = self.create_resource(
            'sample2', sample_meta_dir, {'ip': '10.0.0.2'}
        )
        xs.connect(sample1, sample2)

        with self.assertRaises(Exception):
            xs.connect(sample2, sample1)


class TestListInput(base.BaseResourceTest):

    def test_list_input_single(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  ip:
    schema: str
    value:
        """)
        list_input_single_meta_dir = self.make_resource_meta("""
id: list-input-single
handler: ansible
version: 1.0.0
input:
  ips:
    schema: [str]
    value: []
        """)

        sample1 = self.create_resource(
            'sample1', sample_meta_dir, {'ip': '10.0.0.1'}
        )
        sample2 = self.create_resource(
            'sample2', sample_meta_dir, {'ip': '10.0.0.2'}
        )
        list_input_single = self.create_resource(
            'list-input-single', list_input_single_meta_dir, {'ips': []}
        )

        sample1.connect(list_input_single, mapping={'ip': 'ips'})
        self.assertItemsEqual(
            #[ip['value'] for ip in list_input_single.args['ips']],
            list_input_single.args['ips'],
            [
                sample1.args['ip'],
            ]
        )
        # self.assertListEqual(
        #    [(e['emitter_attached_to'], e['emitter']) for e in list_input_single.args['ips']],
        #    [(sample1.args['ip'].attached_to.name, 'ip')]
        #)

        sample2.connect(list_input_single, mapping={'ip': 'ips'})
        self.assertItemsEqual(
            #[ip['value'] for ip in list_input_single.args['ips']],
            list_input_single.args['ips'],
            [
                sample1.args['ip'],
                sample2.args['ip'],
            ]
        )
        # self.assertListEqual(
        #    [(e['emitter_attached_to'], e['emitter']) for e in list_input_single.args['ips']],
        #    [(sample1.args['ip'].attached_to.name, 'ip'),
        #     (sample2.args['ip'].attached_to.name, 'ip')]
        #)

        # Test update
        sample2.update({'ip': '10.0.0.3'})
        self.assertItemsEqual(
            #[ip['value'] for ip in list_input_single.args['ips']],
            list_input_single.args['ips'],
            [
                sample1.args['ip'],
                sample2.args['ip'],
            ]
        )

        # Test disconnect
        sample2.disconnect(list_input_single)
        self.assertItemsEqual(
            #[ip['value'] for ip in list_input_single.args['ips']],
            list_input_single.args['ips'],
            [
                sample1.args['ip'],
            ]
        )
        # self.assertListEqual(
        #    [(e['emitter_attached_to'], e['emitter']) for e in list_input_single.args['ips']],
        #    [(sample1.args['ip'].attached_to.name, 'ip')]
        #)

    def test_list_input_multi(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  ip:
    schema: str
    value:
  port:
    schema: int
    value:
        """)
        list_input_multi_meta_dir = self.make_resource_meta("""
id: list-input-multi
handler: ansible
version: 1.0.0
input:
  ips:
    schema: [str]
    value:
  ports:
    schema: [int]
    value:
        """)

        sample1 = self.create_resource(
            'sample1', sample_meta_dir, {'ip': '10.0.0.1', 'port': 1000}
        )
        sample2 = self.create_resource(
            'sample2', sample_meta_dir, {'ip': '10.0.0.2', 'port': 1001}
        )
        list_input_multi = self.create_resource(
            'list-input-multi', list_input_multi_meta_dir, args={'ips': [], 'ports': []}
        )

        xs.connect(sample1, list_input_multi, mapping={
                   'ip': 'ips', 'port': 'ports'})
        self.assertItemsEqual(
            #[ip['value'] for ip in list_input_multi.args['ips']],
            list_input_multi.args['ips'],
            [sample1.args['ip']]
        )
        self.assertItemsEqual(
            #[p['value'] for p in list_input_multi.args['ports']],
            list_input_multi.args['ports'],
            [sample1.args['port']]
        )

        xs.connect(sample2, list_input_multi, mapping={
                   'ip': 'ips', 'port': 'ports'})
        self.assertItemsEqual(
            #[ip['value'] for ip in list_input_multi.args['ips']],
            list_input_multi.args['ips'],
            [
                sample1.args['ip'],
                sample2.args['ip'],
            ]
        )
        # self.assertListEqual(
        #    [(e['emitter_attached_to'], e['emitter']) for e in list_input_multi.args['ips']],
        #    [(sample1.args['ip'].attached_to.name, 'ip'),
        #     (sample2.args['ip'].attached_to.name, 'ip')]
        #)
        self.assertItemsEqual(
            #[p['value'] for p in list_input_multi.args['ports']],
            list_input_multi.args['ports'],
            [
                sample1.args['port'],
                sample2.args['port'],
            ]
        )
        # self.assertListEqual(
        #    [(e['emitter_attached_to'], e['emitter']) for e in list_input_multi.args['ports']],
        #    [(sample1.args['port'].attached_to.name, 'port'),
        #     (sample2.args['port'].attached_to.name, 'port')]
        #)

        # Test disconnect
        sample2.disconnect(list_input_multi)
        self.assertItemsEqual(
            #[ip['value'] for ip in list_input_multi.args['ips']],
            list_input_multi.args['ips'],
            [sample1.args['ip']]
        )
        self.assertItemsEqual(
            #[p['value'] for p in list_input_multi.args['ports']],
            list_input_multi.args['ports'],
            [sample1.args['port']]
        )

# XXX: not used for now, not implemented in new db (jnowak)
#     @pytest.mark.xfail(reason="Nested lists are not supported in new_db")
#     def test_nested_list_input(self):
#         """
#         Make sure that single input change is propagated along the chain of
#         lists.
#         """

#         sample_meta_dir = self.make_resource_meta("""
# id: sample
# handler: ansible
# version: 1.0.0
# input:
#   ip:
#     schema: str
#     value:
#   port:
#     schema: int
#     value:
#         """)
#         list_input_meta_dir = self.make_resource_meta("""
# id: list-input
# handler: ansible
# version: 1.0.0
# input:
#   ips:
#     schema: [str]
#     value: []
#   ports:
#     schema: [int]
#     value: []
#         """)
#         list_input_nested_meta_dir = self.make_resource_meta("""
# id: list-input-nested
# handler: ansible
# version: 1.0.0
# input:
#   ipss:
#     schema: [[str]]
#     value: []
#   portss:
#     schema: [[int]]
#     value: []
#         """)

#         sample1 = self.create_resource(
#             'sample1', sample_meta_dir, {'ip': '10.0.0.1', 'port': 1000}
#         )
#         sample2 = self.create_resource(
#             'sample2', sample_meta_dir, {'ip': '10.0.0.2', 'port': 1001}
#         )
#         list_input = self.create_resource(
#             'list-input', list_input_meta_dir,
#         )
#         list_input_nested = self.create_resource(
#             'list-input-nested', list_input_nested_meta_dir,
#         )

#         sample1.connect(list_input, mapping={'ip': 'ips', 'port': 'ports'})
#         sample2.connect(list_input, mapping={'ip': 'ips', 'port': 'ports'})
#         list_input.connect(list_input_nested, mapping={'ips': 'ipss', 'ports': 'portss'})
#         self.assertListEqual(
#             #[ips['value'] for ips in list_input_nested.args['ipss']],
#             list_input_nested.args['ipss'],
#             [list_input.args['ips']]
#         )
#         self.assertListEqual(
#             #[ps['value'] for ps in list_input_nested.args['portss']],
#             list_input_nested.args['portss'],
#             [list_input.args['ports']]
#         )

#         # Test disconnect
#         xs.disconnect(sample1, list_input)
#         self.assertListEqual(
#             #[[ip['value'] for ip in ips['value']] for ips in list_input_nested.args['ipss']],
#             list_input_nested.args['ipss'],
#             [[sample2.args['ip']]]
#         )
#         self.assertListEqual(
#             list_input_nested.args['portss'],
#             [[sample2.args['port']]]
#         )


class TestHashInput(base.BaseResourceTest):

    @pytest.mark.xfail(reason="Connect should raise an error if already connected")
    def test_hash_input_basic(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
    ip:
        schema: str!
        value:
    port:
        schema: int!
        value:
        """)
        receiver_meta_dir = self.make_resource_meta("""
id: receiver
handler: ansible
version: 1.0.0
input:
    server:
        schema: {ip: str!, port: int!}
        """)

        sample1 = self.create_resource(
            'sample1', sample_meta_dir, args={'ip': '10.0.0.1', 'port': 5000}
        )
        sample2 = self.create_resource(
            'sample2', sample_meta_dir, args={'ip': '10.0.0.2', 'port': 5001}
        )
        sample3 = self.create_resource(
            'sample3', sample_meta_dir, args={'ip': '10.0.0.3', 'port': 5002}
        )
        receiver = self.create_resource(
            'receiver', receiver_meta_dir
        )
        xs.connect(sample1, receiver, mapping={
                   'ip': 'server:ip', 'port': 'server:port'})
        self.assertDictEqual(
            {'ip': sample1.args['ip'], 'port': sample1.args['port']},
            receiver.args['server'],
        )
        sample1.update({'ip': '10.0.0.2'})
        self.assertDictEqual(
            {'ip': sample1.args['ip'], 'port': sample1.args['port']},
            receiver.args['server'],
        )
        # XXX: We need to disconnect first
        # XXX: it should raise error when connecting already connected inputs
        xs.connect(sample2, receiver, mapping={'ip': 'server:ip'})
        self.assertDictEqual(
            {'ip': sample2.args['ip'], 'port': sample1.args['port']},
            receiver.args['server'],
        )
        xs.connect(sample3, receiver, mapping={
                   'ip': 'server:ip', 'port': 'server:port'})
        self.assertDictEqual(
            {'ip': sample3.args['ip'], 'port': sample3.args['port']},
            receiver.args['server'],
        )

    def test_hash_input_mixed(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
    ip:
        schema: str!
        value:
    port:
        schema: int!
        value:
        """)
        receiver_meta_dir = self.make_resource_meta("""
id: receiver
handler: ansible
version: 1.0.0
input:
    server:
        schema: {ip: str!, port: int!}
        """)

        sample = self.create_resource(
            'sample', sample_meta_dir, args={'ip': '10.0.0.1', 'port': 5000}
        )
        receiver = self.create_resource(
            'receiver', receiver_meta_dir, args={'server': {'port': 5001}}
        )
        sample.connect(receiver, mapping={'ip': 'server:ip'})
        self.assertDictEqual(
            {'ip': sample.args['ip'], 'port': 5001},
            receiver.args['server'],
        )
        sample.update({'ip': '10.0.0.2'})
        self.assertDictEqual(
            {'ip': sample.args['ip'], 'port': 5001},
            receiver.args['server'],
        )

    def test_hash_input_with_list(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
    ip:
        schema: str!
        value:
    port:
        schema: int!
        value:
        """)
        receiver_meta_dir = self.make_resource_meta("""
id: receiver
handler: ansible
version: 1.0.0
input:
    server:
        schema: [{ip: str!, port: int!}]
        """)

        sample1 = self.create_resource(
            'sample1', sample_meta_dir, args={'ip': '10.0.0.1', 'port': 5000}
        )
        receiver = self.create_resource(
            'receiver', receiver_meta_dir
        )
        xs.connect(sample1, receiver, mapping={
                   'ip': 'server:ip', 'port': 'server:port'})
        self.assertItemsEqual(
            [{'ip': sample1.args['ip'], 'port': sample1.args['port']}],
            receiver.args['server'],
        )
        sample2 = self.create_resource(
            'sample2', sample_meta_dir, args={'ip': '10.0.0.2', 'port': 5001}
        )
        xs.connect(sample2, receiver, mapping={
                   'ip': 'server:ip', 'port': 'server:port'})
        self.assertItemsEqual(
            [{'ip': sample1.args['ip'], 'port': sample1.args['port']},
             {'ip': sample2.args['ip'], 'port': sample2.args['port']}],
            receiver.args['server'],
        )
        sample1.disconnect(receiver)
        self.assertItemsEqual(
            [{'ip': sample2.args['ip'], 'port': sample2.args['port']}],
            receiver.args['server'],
        )

    def test_hash_input_with_multiple_connections(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
    ip:
        schema: str!
        value:
        """)
        receiver_meta_dir = self.make_resource_meta("""
id: receiver
handler: ansible
version: 1.0.0
input:
    ip:
        schema: str!
        value:
    server:
        schema: {ip: str!}
        """)

        sample = self.create_resource(
            'sample', sample_meta_dir, args={'ip': '10.0.0.1'}
        )
        receiver = self.create_resource(
            'receiver', receiver_meta_dir
        )
        xs.connect(sample, receiver, mapping={'ip': ['ip', 'server:ip']})
        self.assertEqual(
            sample.args['ip'],
            receiver.args['ip']
        )
        self.assertDictEqual(
            {'ip': sample.args['ip']},
            receiver.args['server'],
        )

    def test_hash_input_multiple_resources_with_tag_connect(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
    ip:
        schema: str!
        value:
    port:
        schema: int!
        value:
        """)
        receiver_meta_dir = self.make_resource_meta("""
id: receiver
handler: ansible
version: 1.0.0
input:
    server:
        schema: [{ip: str!, port: int!}]
        """)

        sample1 = self.create_resource(
            'sample1', sample_meta_dir, args={'ip': '10.0.0.1', 'port': 5000}
        )
        sample2 = self.create_resource(
            'sample2', sample_meta_dir, args={'ip': '10.0.0.2', 'port': 5001}
        )
        receiver = self.create_resource(
            'receiver', receiver_meta_dir
        )
        sample1.connect(receiver, mapping={'ip': 'server:ip'})
        sample2.connect(receiver, mapping={'port': 'server:port|sample1'})
        self.assertItemsEqual(
            [{'ip': sample1.args['ip'], 'port': sample2.args['port']}],
            receiver.args['server'],
        )
        sample3 = self.create_resource(
            'sample3', sample_meta_dir, args={'ip': '10.0.0.3', 'port': 5002}
        )
        sample3.connect(receiver, mapping={
                        'ip': 'server:ip', 'port': 'server:port'})
        self.assertItemsEqual(
            [{'ip': sample1.args['ip'], 'port': sample2.args['port']},
             {'ip': sample3.args['ip'], 'port': sample3.args['port']}],
            receiver.args['server'],
        )
        sample4 = self.create_resource(
            'sample4', sample_meta_dir, args={'ip': '10.0.0.4', 'port': 5003}
        )
        sample4.connect(receiver, mapping={'port': 'server:port|sample3'})
        self.assertItemsEqual(
            [{'ip': sample1.args['ip'], 'port': sample2.args['port']},
             {'ip': sample3.args['ip'], 'port': sample4.args['port']}],
            receiver.args['server'],
        )
        # There can be no sample3 connections left now
        sample4.connect(receiver, mapping={'ip': 'server:ip|sample3'})
        self.assertItemsEqual(
            [{'ip': sample1.args['ip'], 'port': sample2.args['port']},
             {'ip': sample4.args['ip'], 'port': sample4.args['port']}],
            receiver.args['server'],
        )
