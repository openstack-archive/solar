import click
import requests
import sys
import time

from solar.core import actions
from solar.core import resource
from solar.core.resource_provider import  GitProvider
from solar.core import signals
from solar.core import validation

from solar.interfaces.db import get_db


GIT_PUPPET_LIBS_URL = 'https://github.com/CGenie/puppet-libs-resource'
GIT_KEYSTONE_PUPPET_RESOURCE_URL = 'https://github.com/CGenie/keystone-puppet-resource'


@click.group()
def main():
    pass


@click.command()
def deploy():
    db = get_db()
    db.clear()

    signals.Connections.clear()

    node1 = resource.create('node1', 'resources/ro_node/', {'ip': '10.0.0.3', 'ssh_key': '/vagrant/.vagrant/machines/solar-dev1/virtualbox/private_key', 'ssh_user': 'vagrant'})

    puppet_inifile = resource.create('puppet_inifile', GitProvider(GIT_PUPPET_LIBS_URL, path='puppet_inifile'), {})
    puppet_mysql = resource.create('puppet_mysql', GitProvider(GIT_PUPPET_LIBS_URL, path='puppet_mysql'), {})
    puppet_stdlib = resource.create('puppet_stdlib', GitProvider(GIT_PUPPET_LIBS_URL, path='puppet_stdlib'), {})

    mariadb_service1 = resource.create('mariadb_service1', 'resources/mariadb_service', {'image': 'mariadb', 'root_password': 'mariadb', 'port': 3306})
    keystone_db = resource.create('keystone_db', 'resources/mariadb_keystone_db/', {'db_name': 'keystone_db', 'login_user': 'root'})
    keystone_db_user = resource.create('keystone_db_user', 'resources/mariadb_keystone_user/', {'new_user_name': 'keystone', 'new_user_password': 'keystone', 'login_user': 'root'})

    keystone_puppet = resource.create('keystone_config1', GitProvider(GIT_KEYSTONE_PUPPET_RESOURCE_URL, path='keystone_puppet'), {})

    signals.connect(node1, puppet_inifile)
    signals.connect(node1, puppet_mysql)
    signals.connect(node1, puppet_stdlib)

    signals.connect(node1, mariadb_service1)
    signals.connect(node1, keystone_db)
    signals.connect(node1, keystone_db_user)
    signals.connect(mariadb_service1, keystone_db, {'port': 'login_port', 'root_password': 'login_password'})
    signals.connect(mariadb_service1, keystone_db_user, {'port': 'login_port', 'root_password': 'login_password'})
    signals.connect(keystone_db, keystone_db_user, {'db_name': 'db_name'})

    signals.connect(node1, keystone_puppet)
    signals.connect(keystone_db, keystone_puppet, {'db_name': 'db_name'})
    signals.connect(keystone_db_user, keystone_puppet, {'new_user_name': 'db_user', 'new_user_password': 'db_password'})


    has_errors = False
    for r in locals().values():
        if not isinstance(r, resource.Resource):
            continue

        print 'Validating {}'.format(r.name)
        errors = validation.validate_resource(r)
        if errors:
            has_errors = True
            print 'ERROR: %s: %s' % (r.name, errors)

    if has_errors:
        sys.exit(1)


    # run
    actions.resource_action(puppet_inifile, 'run')
    actions.resource_action(puppet_mysql, 'run')
    actions.resource_action(puppet_stdlib, 'run')
    actions.resource_action(mariadb_service1, 'run')
    actions.resource_action(keystone_db, 'run')
    actions.resource_action(keystone_db_user, 'run')
    actions.resource_action(keystone_puppet, 'run')
    time.sleep(10)

    # test working configuration
    #requests.get('http://%s:%s' % (keystone_service1.args['ip'].value, keystone_service1.args['port'].value))
    #requests.get('http://%s:%s' % (keystone_service2.args['ip'].value, keystone_service2.args['port'].value))
    #requests.get('http://%s:%s' % (haproxy_service.args['ip'].value, haproxy_service.args['ports'].value[0]['value'][0]['value']))
    requests.get('http://%s:%s' % (keystone_puppet.args['ip'].value, keystone_puppet.args['port'].value))

    # token_data = requests.post(
    #     'http://%s:%s/v2.0/tokens' % (keystone_puppet.args['ip'].value, 5000),
    #     json.dumps({
    #         'auth': {
    #             'tenantName': glance_keystone_user.args['tenant_name'].value,
    #             'passwordCredentials': {
    #                 'username': glance_keystone_user.args['user_name'].value,
    #                 'password': glance_keystone_user.args['user_password'].value,
    #             }
    #         }
    #     }),
    #     headers={'Content-Type': 'application/json'}
    # )

    # token = token_data.json()['access']['token']['id']
    # print 'TOKEN: {}'.format(token)


@click.command()
def undeploy():
    db = get_db()

    resources = map(resource.wrap_resource, db.get_list(collection=db.COLLECTIONS.resource))
    resources = {r.name: r for r in resources}

    actions.resource_action(resources['keystone_puppet'], 'remove')
    actions.resource_action(resources['keystone_db_user'], 'remove')
    actions.resource_action(resources['keystone_db'], 'remove')
    actions.resource_action(resources['mariadb_service1'], 'remove')
    actions.resource_action(resources['puppet_stdlib'], 'remove')
    actions.resource_action(resources['puppet_mysql'], 'remove')
    actions.resource_action(resources['puppet_inifile'], 'remove')

    db.clear()

    signals.Connections.clear()


main.add_command(deploy)
main.add_command(undeploy)


if __name__ == '__main__':
    main()
