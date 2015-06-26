import click
import json
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


@click.group()
def main():
    pass


@click.command()
def deploy():
    db = get_db()
    db.clear()

    signals.Connections.clear()

    node1 = resource.create('node1', 'resources/ro_node/', {'ip': '10.0.0.3', 'ssh_key': '/vagrant/.vagrant/machines/solar-dev1/virtualbox/private_key', 'ssh_user': 'vagrant'})

    rabbitmq_service1 = resource.create('rabbitmq_service1', 'resources/rabbitmq_service/', {'management_port': 15672, 'port': 5672, 'container_name': 'rabbitmq_service1', 'image': 'rabbitmq:3-management'})
    openstack_vhost = resource.create('openstack_vhost', 'resources/rabbitmq_vhost/', {'vhost_name': 'openstack'})
    openstack_rabbitmq_user = resource.create('openstack_rabbitmq_user', 'resources/rabbitmq_user/', {'user_name': 'openstack', 'password': 'openstack_password'})

    puppet_inifile = resource.create('puppet_inifile', GitProvider(GIT_PUPPET_LIBS_URL, path='inifile'), {})
    puppet_mysql = resource.create('puppet_mysql', GitProvider(GIT_PUPPET_LIBS_URL, path='mysql'), {})
    puppet_stdlib = resource.create('puppet_stdlib', GitProvider(GIT_PUPPET_LIBS_URL, path='stdlib'), {})

    mariadb_service1 = resource.create('mariadb_service1', 'resources/mariadb_service', {'image': 'mariadb', 'root_password': 'mariadb', 'port': 3306})
    keystone_db = resource.create('keystone_db', 'resources/mariadb_keystone_db/', {'db_name': 'keystone_db', 'login_user': 'root'})
    keystone_db_user = resource.create('keystone_db_user', 'resources/mariadb_keystone_user/', {'new_user_name': 'keystone', 'new_user_password': 'keystone', 'login_user': 'root'})

    keystone_puppet = resource.create('keystone_puppet', GitProvider(GIT_PUPPET_LIBS_URL, path='keystone'), {})
    #keystone_puppet = resource.create('keystone_puppet', 'resources/keystone_puppet', {})

    # TODO: vhost cannot be specified in neutron Puppet manifests so this user has to be admin anyways
    neutron_puppet = resource.create('neutron_puppet', GitProvider(GIT_PUPPET_LIBS_URL, path='neutron'), {'rabbitmq_user': 'guest', 'rabbitmq_password': 'guest'})
    #neutron_puppet = resource.create('neutron_puppet', 'resources/neutron_puppet', {'rabbitmq_user': 'guest', 'rabbitmq_password': 'guest'})

    admin_tenant = resource.create('admin_tenant', 'resources/keystone_tenant', {'tenant_name': 'admin'})
    admin_user = resource.create('admin_user', 'resources/keystone_user', {'user_name': 'admin', 'user_password': 'admin'})
    admin_role = resource.create('admin_role', 'resources/keystone_role', {'role_name': 'admin'})

    services_tenant = resource.create('services_tenant', 'resources/keystone_tenant', {'tenant_name': 'services'})
    neutron_keystone_user = resource.create('neutron_keystone_user', 'resources/keystone_user', {'user_name': 'neutron', 'user_password': 'neutron'})
    neutron_keystone_role = resource.create('neutron_keystone_role', 'resources/keystone_role', {'role_name': 'neutron'})

    neutron_keystone_service_endpoint = resource.create('neutron_keystone_service_endpoint', 'resources/keystone_service_endpoint', {'adminurl': 'http://{{ip}}:{{admin_port}}', 'internalurl': 'http://{{ip}}:{{port}}', 'publicurl': 'http://{{ip}}:{{port}}', 'description': 'OpenStack Network Service', 'type': 'network', 'port': 9696, 'admin_port': 9696})

    #cinder_puppet = resource.create('cinder_puppet', GitProvider(GIT_PUPPET_LIBS_URL, 'cinder'), {})
    cinder_puppet = resource.create('cinder_puppet', 'resources/cinder_puppet', {})

    cinder_keystone_user = resource.create('cinder_keystone_user', 'resources/keystone_user', {'user_name': 'cinder', 'user_password': 'cinder'})
    cinder_keystone_role = resource.create('cinder_keystone_role', 'resources/keystone_role', {'role_name': 'cinder'})

    #nova_puppet = resource.create('nova_puppet', GitProvider(GIT_PUPPET_LIBS_URL, 'nova'), {'rabbitmq_user': 'guest', 'rabbitmq_password': 'guest'})
    # TODO: fix rabbitmq user/password
    nova_puppet = resource.create('nova_puppet', 'resources/nova_puppet', {'rabbitmq_user': 'guest', 'rabbitmq_password': 'guest'})

    nova_keystone_user = resource.create('nova_keystone_user', 'resources/keystone_user', {'user_name': 'nova', 'user_password': 'nova'})
    nova_keystone_role = resource.create('nova_keystone_role', 'resources/keystone_role', {'role_name': 'nova'})

    # TODO: 'services' tenant-id is hardcoded
    nova_keystone_service_endpoint = resource.create('nova_keystone_service_endpoint', 'resources/keystone_service_endpoint', {'adminurl': 'http://{{ip}}:{{admin_port}}/v2/services', 'internalurl': 'http://{{ip}}:{{port}}/v2/services', 'publicurl': 'http://{{ip}}:{{port}}/v2/services', 'description': 'OpenStack Compute Service', 'type': 'compute', 'port': 8776, 'admin_port': 8776})


    signals.connect(node1, rabbitmq_service1)
    signals.connect(rabbitmq_service1, openstack_vhost)
    signals.connect(rabbitmq_service1, openstack_rabbitmq_user)
    signals.connect(openstack_vhost, openstack_rabbitmq_user, {'vhost_name': 'vhost_name'})
    signals.connect(rabbitmq_service1, neutron_puppet, {'ip': 'rabbitmq_host', 'port': 'rabbitmq_port'})
    signals.connect(openstack_vhost, cinder_puppet, {'vhost_name': 'rabbitmq_vhost'})
    signals.connect(openstack_rabbitmq_user, cinder_puppet, {'user_name': 'rabbitmq_user', 'password': 'rabbitmq_password'})
    signals.connect(rabbitmq_service1, cinder_puppet, {'ip': 'rabbitmq_host', 'port': 'rabbitmq_port'})
    signals.connect(rabbitmq_service1, nova_puppet, {'ip': 'rabbitmq_host', 'port': 'rabbitmq_port'})

    signals.connect(node1, puppet_inifile)
    signals.connect(node1, puppet_mysql)
    signals.connect(node1, puppet_stdlib)

    signals.connect(node1, mariadb_service1)
    signals.connect(node1, keystone_db)
    signals.connect(node1, keystone_db_user)
    signals.connect(mariadb_service1, keystone_db, {'port': 'login_port', 'root_password': 'login_password'})
    signals.connect(mariadb_service1, keystone_db_user, {'port': 'login_port', 'root_password': 'login_password'})
    signals.connect(keystone_db, keystone_db_user, {'db_name': 'db_name'})

    signals.connect(keystone_puppet, admin_tenant)
    signals.connect(keystone_puppet, admin_tenant, {'admin_port': 'keystone_port', 'ip': 'keystone_host'})
    signals.connect(admin_tenant, admin_user)
    signals.connect(admin_user, admin_role)

    signals.connect(keystone_puppet, services_tenant)
    signals.connect(keystone_puppet, services_tenant, {'admin_port': 'keystone_port', 'ip': 'keystone_host'})
    signals.connect(services_tenant, neutron_keystone_user)
    signals.connect(neutron_keystone_user, neutron_keystone_role)

    signals.connect(node1, keystone_puppet)
    signals.connect(keystone_db, keystone_puppet, {'db_name': 'db_name'})
    signals.connect(keystone_db_user, keystone_puppet, {'new_user_name': 'db_user', 'new_user_password': 'db_password'})

    # NEUTRON
    signals.connect(node1, neutron_puppet)
    signals.connect(admin_user, neutron_puppet, {'user_name': 'keystone_user', 'user_password': 'keystone_password', 'tenant_name': 'keystone_tenant'})
    signals.connect(keystone_puppet, neutron_puppet, {'ip': 'keystone_host', 'port': 'keystone_port'})

    signals.connect(neutron_puppet, neutron_keystone_service_endpoint, {'ip': 'ip', 'ssh_key': 'ssh_key', 'ssh_user': 'ssh_user'})
    #signals.connect(neutron_puppet, neutron_keystone_service_endpoint, {'port': 'admin_port'})
    signals.connect(keystone_puppet, neutron_keystone_service_endpoint, {'ip': 'keystone_host', 'admin_port': 'keystone_port', 'admin_token': 'admin_token'})

    # CINDER
    signals.connect(node1, cinder_puppet)
    signals.connect(keystone_puppet, cinder_puppet, {'ip': 'keystone_host', 'port': 'keystone_port'})

    signals.connect(services_tenant, cinder_keystone_user)
    signals.connect(cinder_keystone_user, cinder_keystone_role)

    signals.connect(cinder_keystone_user, cinder_puppet, {'user_name': 'keystone_user', 'user_password': 'keystone_password', 'tenant_name': 'keystone_tenant'})

    # NOVA
    signals.connect(node1, nova_puppet)

    signals.connect(services_tenant, nova_keystone_user)
    signals.connect(neutron_keystone_user, nova_keystone_role)

    signals.connect(nova_keystone_user, nova_puppet, {'user_name': 'keystone_user', 'user_password': 'keystone_password', 'tenant_name': 'keystone_tenant'})
    signals.connect(keystone_puppet, nova_puppet, {'ip': 'keystone_host', 'port': 'keystone_port'})

    signals.connect(nova_puppet, nova_keystone_service_endpoint, {'ip': 'ip', 'ssh_key': 'ssh_key', 'ssh_user': 'ssh_user'})
    signals.connect(keystone_puppet, nova_keystone_service_endpoint, {'ip': 'keystone_host', 'admin_port': 'keystone_port', 'admin_token': 'admin_token'})


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
    actions.resource_action(rabbitmq_service1, 'run')
    actions.resource_action(openstack_vhost, 'run')
    actions.resource_action(openstack_rabbitmq_user, 'run')

    actions.resource_action(puppet_inifile, 'run')
    actions.resource_action(puppet_mysql, 'run')
    actions.resource_action(puppet_stdlib, 'run')

    actions.resource_action(mariadb_service1, 'run')

    actions.resource_action(keystone_db, 'run')
    actions.resource_action(keystone_db_user, 'run')
    actions.resource_action(keystone_puppet, 'run')

    actions.resource_action(admin_tenant, 'run')
    actions.resource_action(admin_user, 'run')
    actions.resource_action(admin_role, 'run')

    actions.resource_action(services_tenant, 'run')
    actions.resource_action(neutron_keystone_user, 'run')
    actions.resource_action(neutron_keystone_role, 'run')

    actions.resource_action(neutron_puppet, 'run')
    actions.resource_action(neutron_keystone_service_endpoint, 'run')

    actions.resource_action(cinder_keystone_user, 'run')
    actions.resource_action(cinder_keystone_role, 'run')

    actions.resource_action(cinder_puppet, 'run')

    actions.resource_action(nova_keystone_user, 'run')
    actions.resource_action(nova_keystone_role, 'run')

    actions.resource_action(nova_puppet, 'run')
    actions.resource_action(nova_keystone_service_endpoint, 'run')

    time.sleep(10)

    # test working configuration
    #requests.get('http://%s:%s' % (keystone_service1.args['ip'].value, keystone_service1.args['port'].value))
    #requests.get('http://%s:%s' % (keystone_service2.args['ip'].value, keystone_service2.args['port'].value))
    #requests.get('http://%s:%s' % (haproxy_service.args['ip'].value, haproxy_service.args['ports'].value[0]['value'][0]['value']))
    requests.get('http://%s:%s' % (keystone_puppet.args['ip'].value, keystone_puppet.args['port'].value))

    for service_name in ['admin', 'neutron', 'cinder', 'nova']:
        if service_name == 'admin':
            tenant = admin_tenant.args['tenant_name'].value
        else:
            tenant = services_tenant.args['tenant_name'].value

        if service_name == 'admin':
            user = admin_user
        elif service_name == 'neutron':
            user = neutron_keystone_user
        elif service_name == 'cinder':
            user = cinder_keystone_user
        elif service_name == 'nova':
            user = nova_keystone_user

        token_data = requests.post(
            'http://%s:%s/v2.0/tokens' % (keystone_puppet.args['ip'].value, 5000),
            json.dumps({
                'auth': {
                    'tenantName': tenant,
                    'passwordCredentials': {
                        'username': user.args['user_name'].value,
                        'password': user.args['user_password'].value,
                    },
                },
            }),
            headers={'Content-Type': 'application/json'}
        )

        token = token_data.json()['access']['token']['id']
        print '{} TOKEN: {}'.format(service_name.upper(), token)

    # neutron_token_data = requests.post(
    #     'http://%s:%s/v2.0/tokens' % (keystone_puppet.args['ip'].value, 5000),
    #     json.dumps({
    #         'auth': {
    #             'tenantName': services_tenant.args['tenant_name'].value,
    #             'passwordCredentials': {
    #                 'username': neutron_keystone_user.args['user_name'].value,
    #                 'password': neutron_keystone_user.args['user_password'].value,
    #             },
    #         },
    #     }),
    #     headers={'Content-Type': 'application/json'}
    # )
    #
    # neutron_token = neutron_token_data.json()['access']['token']['id']
    # print 'NEUTRON TOKEN: {}'.format(neutron_token)


@click.command()
def undeploy():
    db = get_db()

    resources = map(resource.wrap_resource, db.get_list(collection=db.COLLECTIONS.resource))
    resources = {r.name: r for r in resources}

    actions.resource_action(resources['nova_keystone_service_endpoint'], 'remove' )
    actions.resource_action(resources['nova_puppet'], 'remove' )

    actions.resource_action(resources['nova_keystone_role'], 'remove')
    actions.resource_action(resources['nova_keystone_user'], 'remove')

    actions.resource_action(resources['cinder_puppet'], 'remove' )

    actions.resource_action(resources['neutron_keystone_service_endpoint'], 'remove' )
    actions.resource_action(resources['neutron_puppet'], 'remove' )

    actions.resource_action(resources['cinder_keystone_role'], 'remove')
    actions.resource_action(resources['cinder_keystone_user'], 'remove')

    actions.resource_action(resources['neutron_keystone_role'], 'remove')
    actions.resource_action(resources['neutron_keystone_user'], 'remove')
    actions.resource_action(resources['services_tenant'], 'remove')

    actions.resource_action(resources['admin_role'], 'remove')
    actions.resource_action(resources['admin_user'], 'remove')
    actions.resource_action(resources['admin_tenant'], 'remove')

    actions.resource_action(resources['keystone_puppet'], 'remove')
    actions.resource_action(resources['keystone_db_user'], 'remove')
    actions.resource_action(resources['keystone_db'], 'remove')

    actions.resource_action(resources['mariadb_service1'], 'remove')

    actions.resource_action(resources['puppet_stdlib'], 'remove')
    actions.resource_action(resources['puppet_mysql'], 'remove')
    actions.resource_action(resources['puppet_inifile'], 'remove')

    actions.resource_action(resources['openstack_rabbitmq_user'], 'remove')
    actions.resource_action(resources['openstack_vhost'], 'remove')
    actions.resource_action(resources['rabbitmq_service1'], 'remove')

    db.clear()

    signals.Connections.clear()


main.add_command(deploy)
main.add_command(undeploy)


if __name__ == '__main__':
    main()
