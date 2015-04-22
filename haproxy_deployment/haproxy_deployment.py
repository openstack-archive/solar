import unittest

from x import db


class TestHAProxyDeployment(unittest.TestCase):
    def test_keystone_config(self):
        node1 = db.get_resource('node1')
        node2 = db.get_resource('node2')
        keystone1 = db.get_resource('keystone1')
        keystone2 = db.get_resource('keystone2')

        self.assertEqual(keystone1.args['ip'], node1.args['ip'])
        self.assertEqual(keystone2.args['ip'], node2.args['ip'])

    def test_haproxy_keystone_config(self):
        keystone1 = db.get_resource('keystone1')
        keystone2 = db.get_resource('keystone2')
        haproxy_keystone_config = db.get_resource('haproxy_keystone_config')

        self.assertDictEqual(
            haproxy_keystone_config.args['servers'],
            {
                'keystone1': keystone1.args['ip'],
                'keystone2': keystone2.args['ip'],
            }
        )
        self.assertDictEqual(
            haproxy_keystone_config.args['ports'],
            {
                'keystone1': keystone1.args['port'],
                'keystone2': keystone2.args['port'],
            }
        )

    def test_nova_config(self):
        node3 = db.get_resource('node3')
        node4 = db.get_resource('node4')
        nova1 = db.get_resource('nova1')
        nova2 = db.get_resource('nova2')

        self.assertEqual(nova1.args['ip'], node3.args['ip'])
        self.assertEqual(nova2.args['ip'], node4.args['ip'])

    def test_haproxy_nova_config(self):
        nova1 = db.get_resource('nova1')
        nova2 = db.get_resource('nova2')
        haproxy_nova_config = db.get_resource('haproxy_nova_config')

        self.assertDictEqual(
            haproxy_nova_config.args['servers'],
            {
                'nova1': nova1.args['ip'],
                'nova2': nova2.args['ip'],
            }
        )
        self.assertDictEqual(
            haproxy_nova_config.args['ports'],
            {
                'nova1': nova1.args['port'],
                'nova2': nova2.args['port'],
            }
        )

    def test_haproxy(self):
        node5 = db.get_resource('node5')
        haproxy_keystone_config = db.get_resource('haproxy_keystone_config')
        haproxy_nova_config = db.get_resource('haproxy_nova_config')
        haproxy = db.get_resource('haproxy')
        haproxy_config = db.get_resource('haproxy-config')

        self.assertEqual(node5.args['ip'], haproxy.args['ip'])
        self.assertEqual(node5.args['ssh_key'], haproxy.args['ssh_key'])
        self.assertEqual(node5.args['ssh_user'], haproxy.args['ssh_user'])
        self.assertDictEqual(
            haproxy_config.args['configs'],
            {
                'haproxy_keystone_config': haproxy_keystone_config.args['servers'],
                'haproxy_nova_config': haproxy_nova_config.args['servers'],
            }
        )
        self.assertDictEqual(
            haproxy_config.args['configs_ports'],
            {
                'haproxy_keystone_config': haproxy_keystone_config.args['ports'],
                'haproxy_nova_config': haproxy_nova_config.args['ports'],
            }
        )
        self.assertDictEqual(
            haproxy_config.args['listen_ports'],
            {
                'haproxy_keystone_config': haproxy_keystone_config.args['listen_port'],
                'haproxy_nova_config': haproxy_nova_config.args['listen_port'],
            }
        )
        self.assertDictEqual(
            {
                'haproxy-config': haproxy_config.args['config_dir'],
            },
            haproxy.args['host_binds']
        )
        self.assertDictEqual(
            haproxy.args['ports'],
            haproxy_config.args['listen_ports'],
        )


def main():
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestHAProxyDeployment)
    unittest.TextTestRunner().run(suite)