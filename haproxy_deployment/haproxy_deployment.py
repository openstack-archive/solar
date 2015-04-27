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

        self.assertEqual(
            [ip['value'] for ip in haproxy_keystone_config.args['servers'].value],
            [
                keystone1.args['ip'],
                keystone2.args['ip'],
            ]
        )
        self.assertEqual(
            [p['value'] for p in haproxy_keystone_config.args['ports'].value],
            [
                keystone1.args['port'],
                keystone2.args['port'],
            ]
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

        self.assertEqual(
            [ip['value'] for ip in haproxy_nova_config.args['servers'].value],
            [
                nova1.args['ip'],
                nova2.args['ip'],
            ]
        )
        self.assertEqual(
            [p['value'] for p in haproxy_nova_config.args['ports'].value],
            [
                nova1.args['port'],
                nova2.args['port'],
            ]
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
        self.assertEqual(
            [c['value'] for c in haproxy_config.args['configs'].value],
            [
                haproxy_keystone_config.args['servers'],
                haproxy_nova_config.args['servers'],
            ]
        )
        self.assertEqual(
            [cp['value'] for cp in haproxy_config.args['configs_ports'].value],
            [
                haproxy_keystone_config.args['ports'],
                haproxy_nova_config.args['ports'],
            ]
        )
        self.assertEqual(
            [lp['value'] for lp in haproxy_config.args['listen_ports'].value],
            [
                haproxy_keystone_config.args['listen_port'],
                haproxy_nova_config.args['listen_port'],
            ]
        )
        self.assertEqual(
            [
                haproxy_config.args['config_dir'],
            ],
            [hb['value'] for hb in haproxy.args['host_binds'].value]
        )
        self.assertEqual(
            haproxy.args['ports'],
            haproxy_config.args['listen_ports'],
        )


def main():
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestHAProxyDeployment)
    unittest.TextTestRunner().run(suite)