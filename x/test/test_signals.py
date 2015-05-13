import unittest

import base

from x import signals as xs


class TestBaseInput(base.BaseResourceTest):
    def test_input_dict_type(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  values: {}
        """)

        sample1 = self.create_resource(
            'sample1', sample_meta_dir, {'values': {'a': 1, 'b': 2}}
        )
        sample2 = self.create_resource(
            'sample2', sample_meta_dir, {'values': None}
        )
        xs.connect(sample1, sample2)
        self.assertEqual(
            sample1.args['values'],
            sample2.args['values'],
        )
        self.assertEqual(
            sample2.args['values'].emitter,
            sample1.args['values']
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
        xs.disconnect(sample1, sample2)
        sample1.update({'values': {'a': 3}})
        self.assertEqual(
            sample1.args['values'],
            {'a': 3}
        )
        self.assertEqual(
            sample2.args['values'],
            {'a': 2}
        )
        self.assertEqual(sample2.args['values'].emitter, None)

    def test_multiple_resource_disjoint_connect(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  ip:
  port:
        """)
        sample_ip_meta_dir = self.make_resource_meta("""
id: sample-ip
handler: ansible
version: 1.0.0
input:
  ip:
        """)
        sample_port_meta_dir = self.make_resource_meta("""
id: sample-port
handler: ansible
version: 1.0.0
input:
  port:
        """)

        sample = self.create_resource(
            'sample', sample_meta_dir, {'ip': None, 'port': None}
        )
        sample_ip = self.create_resource(
            'sample-ip', sample_ip_meta_dir, {'ip': '10.0.0.1'}
        )
        sample_port = self.create_resource(
            'sample-port', sample_port_meta_dir, {'port': '8000'}
        )
        xs.connect(sample_ip, sample)
        xs.connect(sample_port, sample)
        self.assertEqual(sample.args['ip'], sample_ip.args['ip'])
        self.assertEqual(sample.args['port'], sample_port.args['port'])
        self.assertEqual(
            sample.args['ip'].emitter,
            sample_ip.args['ip']
        )
        self.assertEqual(
            sample.args['port'].emitter,
            sample_port.args['port']
        )

    def test_simple_observer_unsubscription(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  ip:
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
        self.assertEqual(len(sample1.args['ip'].receivers), 1)
        self.assertEqual(
            sample.args['ip'].emitter,
            sample1.args['ip']
        )

        xs.connect(sample2, sample)
        self.assertEqual(sample2.args['ip'], sample.args['ip'])
        # sample should be unsubscribed from sample1 and subscribed to sample2
        self.assertEqual(len(sample1.args['ip'].receivers), 0)
        self.assertEqual(
            sample.args['ip'].emitter,
            sample2.args['ip']
        )

        sample1.update({'ip': '10.0.0.3'})
        self.assertEqual(sample2.args['ip'], sample.args['ip'])

    def test_circular_connection_prevention(self):
        # TODO: more complex cases
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  ip:
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
        """)
        list_input_single_meta_dir = self.make_resource_meta("""
id: list-input-single
handler: ansible
version: 1.0.0
input:
  ips:
input-types:
  ips: list
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

        xs.connect(sample1, list_input_single, mapping={'ip': 'ips'})
        self.assertEqual(
            [ip['value'] for ip in list_input_single.args['ips'].value],
            [
                sample1.args['ip'],
            ]
        )
        self.assertListEqual(
            [(e['emitter_attached_to'], e['emitter']) for e in list_input_single.args['ips'].value],
            [(sample1.args['ip'].attached_to.name, 'ip')]
        )

        xs.connect(sample2, list_input_single, mapping={'ip': 'ips'})
        self.assertEqual(
            [ip['value'] for ip in list_input_single.args['ips'].value],
            [
                sample1.args['ip'],
                sample2.args['ip'],
            ]
        )
        self.assertListEqual(
            [(e['emitter_attached_to'], e['emitter']) for e in list_input_single.args['ips'].value],
            [(sample1.args['ip'].attached_to.name, 'ip'),
             (sample2.args['ip'].attached_to.name, 'ip')]
        )

        # Test update
        sample2.update({'ip': '10.0.0.3'})
        self.assertEqual(
            [ip['value'] for ip in list_input_single.args['ips'].value],
            [
                sample1.args['ip'],
                sample2.args['ip'],
            ]
        )

        # Test disconnect
        xs.disconnect(sample2, list_input_single)
        self.assertEqual(
            [ip['value'] for ip in list_input_single.args['ips'].value],
            [
                sample1.args['ip'],
            ]
        )
        self.assertListEqual(
            [(e['emitter_attached_to'], e['emitter']) for e in list_input_single.args['ips'].value],
            [(sample1.args['ip'].attached_to.name, 'ip')]
        )

    def test_list_input_multi(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  ip:
  port:
        """)
        list_input_multi_meta_dir = self.make_resource_meta("""
id: list-input-multi
handler: ansible
version: 1.0.0
input:
  ips:
  ports:
input-types:
  ips: list
  ports: list
        """)

        sample1 = self.create_resource(
            'sample1', sample_meta_dir, {'ip': '10.0.0.1', 'port': '1000'}
        )
        sample2 = self.create_resource(
            'sample2', sample_meta_dir, {'ip': '10.0.0.2', 'port': '1001'}
        )
        list_input_multi = self.create_resource(
            'list-input-multi', list_input_multi_meta_dir, {'ips': [], 'ports': []}
        )

        xs.connect(sample1, list_input_multi, mapping={'ip': 'ips', 'port': 'ports'})
        self.assertEqual(
            [ip['value'] for ip in list_input_multi.args['ips'].value],
            [sample1.args['ip']]
        )
        self.assertEqual(
            [p['value'] for p in list_input_multi.args['ports'].value],
            [sample1.args['port']]
        )

        xs.connect(sample2, list_input_multi, mapping={'ip': 'ips', 'port': 'ports'})
        self.assertEqual(
            [ip['value'] for ip in list_input_multi.args['ips'].value],
            [
                sample1.args['ip'],
                sample2.args['ip'],
            ]
        )
        self.assertListEqual(
            [(e['emitter_attached_to'], e['emitter']) for e in list_input_multi.args['ips'].value],
            [(sample1.args['ip'].attached_to.name, 'ip'),
             (sample2.args['ip'].attached_to.name, 'ip')]
        )
        self.assertEqual(
            [p['value'] for p in list_input_multi.args['ports'].value],
            [
                sample1.args['port'],
                sample2.args['port'],
            ]
        )
        self.assertListEqual(
            [(e['emitter_attached_to'], e['emitter']) for e in list_input_multi.args['ports'].value],
            [(sample1.args['port'].attached_to.name, 'port'),
             (sample2.args['port'].attached_to.name, 'port')]
        )


'''
class TestMultiInput(base.BaseResourceTest):
    def test_multi_input(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
    ip:
    port:
        """)
        receiver_meta_dir = self.make_resource_meta("""
id: receiver
handler: ansible
version: 1.0.0
input:
    server:
        """)

        sample = self.create_resource(
            'sample', sample_meta_dir, {'ip': '10.0.0.1', 'port': '5000'}
        )
        receiver = self.create_resource(
            'receiver', receiver_meta_dir, {'server': None}
        )
        xs.connect(sample, receiver, mapping={'ip, port': 'server'})
        self.assertItemsEqual(
            (sample.args['ip'], sample.args['port']),
            receiver.args['server'],
        )
'''


if __name__ == '__main__':
    unittest.main()
