import click
import sys
import time

from solar.core import actions
from solar.core import resource
from solar.core.provider import  GitProvider
from solar.core import signals
from solar.core import validation
from solar.core.resource import virtual_resource as vr

from solar.interfaces.db import get_db


GIT_PUPPET_LIBS_URL = 'https://github.com/CGenie/puppet-libs-resource'


# TODO
# Resource for repository OR puppet apt-module in run.pp
# add-apt-repository cloud-archive:juno
# To discuss: install stuff in Docker container

# NOTE
# No copy of manifests, pull from upstream (implemented in the puppet handler)
# Official puppet manifests, not fuel-library


@click.group()
def main():
    pass


@click.command()
def deploy():
    db = get_db()
    db.clear()

    signals.Connections.clear()

    node1 = vr.create('node1', 'resources/ro_node/', {'ip': '10.0.0.3', 'ssh_key': '/vagrant/.vagrant/machines/solar-dev1/virtualbox/private_key', 'ssh_user': 'vagrant'})[0]

    rabbitmq_service1 = vr.create('rabbitmq_service1', 'resources/rabbitmq_service/', {'management_port': 15672, 'port': 5672, 'container_name': 'rabbitmq_service1', 'image': 'rabbitmq:3-management'})[0]
    openstack_vhost = vr.create('openstack_vhost', 'resources/rabbitmq_vhost/', {'vhost_name': 'openstack'})[0]
    openstack_rabbitmq_user = vr.create('openstack_rabbitmq_user', 'resources/rabbitmq_user/', {'user_name': 'openstack', 'password': 'openstack_password'})[0]

    mariadb_service1 = vr.create('mariadb_service1', 'resources/mariadb_service', {'image': 'mariadb', 'root_password': 'mariadb', 'port': 3306})[0]

    signals.connect(node1, mariadb_service1)
    signals.connect(node1, rabbitmq_service1)
    signals.connect(rabbitmq_service1, openstack_vhost)
    signals.connect(rabbitmq_service1, openstack_rabbitmq_user)
    signals.connect(openstack_vhost, openstack_rabbitmq_user, {'vhost_name': 'vhost_name'})

    # KEYSTONE
    keystone_puppet = vr.create('keystone_puppet', 'resources/keystone_puppet', {})[0]
    keystone_db = vr.create('keystone_db', 'resources/mariadb_keystone_db/', {'db_name': 'keystone_db', 'login_user': 'root'})[0]
    keystone_db_user = vr.create('keystone_db_user', 'resources/mariadb_keystone_user/', {'new_user_name': 'keystone', 'new_user_password': 'keystone', 'login_user': 'root'})[0]
    keystone_service_endpoint = vr.create('keystone_service_endpoint', 'resources/keystone_service_endpoint', {'endpoint_name': 'keystone', 'adminurl': 'http://{{admin_ip}}:{{admin_port}}/v2.0', 'internalurl': 'http://{{internal_ip}}:{{internal_port}}/v2.0', 'publicurl': 'http://{{public_ip}}:{{public_port}}/v2.0', 'description': 'OpenStack Identity Service', 'type': 'identity'})[0]

    admin_tenant = vr.create('admin_tenant', 'resources/keystone_tenant', {'tenant_name': 'admin'})[0]
    admin_user = vr.create('admin_user', 'resources/keystone_user', {'user_name': 'admin', 'user_password': 'admin'})[0]
    admin_role = vr.create('admin_role', 'resources/keystone_role', {'role_name': 'admin'})[0]
    services_tenant = vr.create('services_tenant', 'resources/keystone_tenant', {'tenant_name': 'services'})[0]

    signals.connect(node1, rabbitmq_service1)
    signals.connect(rabbitmq_service1, openstack_vhost)
    signals.connect(rabbitmq_service1, openstack_rabbitmq_user)
    signals.connect(openstack_vhost, openstack_rabbitmq_user, {'vhost_name': 'vhost_name'})

    signals.connect(node1, mariadb_service1)
    signals.connect(node1, keystone_db)
    signals.connect(node1, keystone_db_user)
    signals.connect(node1, keystone_puppet)
    signals.connect(mariadb_service1, keystone_db, {'port': 'login_port', 'root_password': 'login_password'})
    signals.connect(mariadb_service1, keystone_db_user, {'port': 'login_port', 'root_password': 'login_password'})
    signals.connect(keystone_db, keystone_db_user, {'db_name': 'db_name'})

    signals.connect(node1, keystone_service_endpoint)
    signals.connect(keystone_puppet, keystone_service_endpoint, {'admin_token': 'admin_token', 'admin_port': 'keystone_admin_port', 'ip': 'keystone_host'})
    signals.connect(keystone_puppet, keystone_service_endpoint, {'admin_port': 'admin_port', 'ip': 'admin_ip'})
    signals.connect(keystone_puppet, keystone_service_endpoint, {'port': 'internal_port', 'ip': 'internal_ip'})
    signals.connect(keystone_puppet, keystone_service_endpoint, {'port': 'public_port', 'ip': 'public_ip'})

    signals.connect(keystone_puppet, admin_tenant)
    signals.connect(keystone_puppet, admin_tenant, {'admin_port': 'keystone_port', 'ip': 'keystone_host'})
    signals.connect(admin_tenant, admin_user)
    signals.connect(admin_user, admin_role)

    signals.connect(keystone_puppet, services_tenant)
    signals.connect(keystone_puppet, services_tenant, {'admin_port': 'keystone_port', 'ip': 'keystone_host'})

    signals.connect(keystone_db, keystone_puppet, {'db_name': 'db_name'})
    signals.connect(keystone_db_user, keystone_puppet, {'new_user_name': 'db_user', 'new_user_password': 'db_password'})

    # NEUTRON
    # TODO: vhost cannot be specified in neutron Puppet manifests so this user has to be admin anyways
    neutron_puppet = vr.create('neutron_puppet', 'resources/neutron_puppet', {'rabbitmq_user': 'guest', 'rabbitmq_password': 'guest'})[0]

    neutron_keystone_user = vr.create('neutron_keystone_user', 'resources/keystone_user', {'user_name': 'neutron', 'user_password': 'neutron'})[0]
    neutron_keystone_role = vr.create('neutron_keystone_role', 'resources/keystone_role', {'role_name': 'neutron'})[0]    
    neutron_keystone_service_endpoint = vr.create('neutron_keystone_service_endpoint', 'resources/keystone_service_endpoint', {'endpoint_name': 'neutron', 'adminurl': 'http://{{admin_ip}}:{{admin_port}}', 'internalurl': 'http://{{internal_ip}}:{{internal_port}}', 'publicurl': 'http://{{public_ip}}:{{public_port}}', 'description': 'OpenStack Network Service', 'type': 'network'})[0]

    signals.connect(node1, neutron_puppet)
    signals.connect(rabbitmq_service1, neutron_puppet, {'ip': 'rabbitmq_host', 'port': 'rabbitmq_port'})
    signals.connect(admin_user, neutron_puppet, {'user_name': 'keystone_user', 'user_password': 'keystone_password', 'tenant_name': 'keystone_tenant'})
    signals.connect(keystone_puppet, neutron_puppet, {'ip': 'keystone_host', 'port': 'keystone_port'})
    signals.connect(services_tenant, neutron_keystone_user)
    signals.connect(neutron_keystone_user, neutron_keystone_role)
    signals.connect(keystone_puppet, neutron_keystone_service_endpoint, {'ip': 'ip', 'ssh_key': 'ssh_key', 'ssh_user': 'ssh_user'})
    signals.connect(neutron_puppet, neutron_keystone_service_endpoint, {'ip': 'admin_ip', 'port': 'admin_port'})
    signals.connect(neutron_puppet, neutron_keystone_service_endpoint, {'ip': 'internal_ip', 'port': 'internal_port'})
    signals.connect(neutron_puppet, neutron_keystone_service_endpoint, {'ip': 'public_ip', 'port': 'public_port'})
    signals.connect(keystone_puppet, neutron_keystone_service_endpoint, {'ip': 'keystone_host', 'admin_port': 'keystone_admin_port', 'admin_token': 'admin_token'})

    # # CINDER
    # cinder_puppet = vr.create('cinder_puppet', 'resources/cinder_puppet', {
    #     'rabbit_userid': 'guest', 'rabbit_password': 'guest'})[0]
    # cinder_db = vr.create('cinder_db', 'resources/mariadb_db/', {
    #     'db_name': 'cinder_db', 'login_user': 'root'})[0]
    # cinder_db_user = vr.create('cinder_db_user', 'resources/mariadb_user/', {
    #     'user_name': 'cinder', 'user_password': 'cinder', 'login_user': 'root'})[0]
    # cinder_keystone_user = vr.create('cinder_keystone_user', 'resources/keystone_user', {
    #     'user_name': 'cinder', 'user_password': 'cinder'})[0]
    # cinder_keystone_role = vr.create('cinder_keystone_role', 'resources/keystone_role', {
    #     'role_name': 'cinder'})[0]
    # cinder_keystone_service_endpoint = vr.create(
    #     'cinder_keystone_service_endpoint', 'resources/keystone_service_endpoint', {
    #         'adminurl': 'http://{{admin_ip}}:{{admin_port}}',
    #         'internalurl': 'http://{{internal_ip}}:{{internal_port}}',
    #         'publicurl': 'http://{{public_ip}}:{{public_port}}',
    #         'description': 'OpenStack Network Service', 'type': 'network'})[0]


    # signals.connect(node1, cinder_db)
    # signals.connect(node1, cinder_db_user)
    # signals.connect(node1, cinder_puppet)
    # signals.connect(rabbitmq_service1, cinder_puppet, {'ip': 'rabbit_host', 'port': 'rabbit_port'})
    # signals.connect(openstack_vhost, cinder_puppet, {'vhost_name': 'rabbit_virtual_host'})
    # signals.connect(openstack_rabbitmq_user, cinder_puppet, {'user_name': 'rabbit_userid', 'password': 'rabbit_password'})
    # signals.connect(mariadb_service1, cinder_db, {
    #     'port': 'login_port', 'root_password': 'login_password'})
    # signals.connect(mariadb_service1, cinder_db_user, {
    #     'port': 'login_port', 'root_password': 'login_password'})
    # signals.connect(cinder_db, cinder_db_user, {'db_name': 'db_name'})

    # signals.connect(services_tenant, cinder_keystone_user)
    # signals.connect(cinder_keystone_user, cinder_keystone_role)

    # NOVA
    # #nova_network_puppet = vr.create('nova_network_puppet', GitProvider(GIT_PUPPET_LIBS_URL, 'nova_network'), {'rabbitmq_user': 'guest', 'rabbitmq_password': 'guest'})[0]
    # # TODO: fix rabbitmq user/password
    # nova_network_puppet = vr.create('nova_network_puppet', 'resources/nova_network_puppet', {'rabbitmq_user': 'guest', 'rabbitmq_password': 'guest'})[0]

    # nova_keystone_user = vr.create('nova_keystone_user', 'resources/keystone_user', {'user_name': 'nova', 'user_password': 'nova'})[0]
    # nova_keystone_role = vr.create('nova_keystone_role', 'resources/keystone_role', {'role_name': 'nova'})[0]

    # TODO: 'services' tenant-id is hardcoded
    # nova_keystone_service_endpoint = vr.create('nova_keystone_service_endpoint', 'resources/keystone_service_endpoint', {'adminurl': 'http://{{ip}}:{{admin_port}}/v2/services', 'internalurl': 'http://{{ip}}:{{public_port}}/v2/services', 'publicurl': 'http://{{ip}}:{{port}}/v2/services', 'description': 'OpenStack Compute Service', 'type': 'compute', 'port': 8776, 'admin_port': 8776})[0]

    # signals.connect(node1, nova_network_puppet)

    # signals.connect(services_tenant, nova_keystone_user)
    # signals.connect(neutron_keystone_user, nova_keystone_role)

    # signals.connect(nova_keystone_user, nova_network_puppet, {'user_name': 'keystone_user', 'user_password': 'keystone_password', 'tenant_name': 'keystone_tenant'})
    # signals.connect(keystone_puppet, nova_network_puppet, {'ip': 'keystone_host', 'port': 'keystone_port'})

    # signals.connect(nova_network_puppet, nova_keystone_service_endpoint, {'ip': 'ip', 'ssh_key': 'ssh_key', 'ssh_user': 'ssh_user'})
    # signals.connect(keystone_puppet, nova_keystone_service_endpoint, {'ip': 'keystone_host', 'admin_port': 'keystone_port', 'admin_token': 'admin_token'})
    # signals.connect(rabbitmq_service1, nova_network_puppet, {'ip': 'rabbitmq_host', 'port': 'rabbitmq_port'})


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

    actions.resource_action(mariadb_service1, 'run')

    actions.resource_action(keystone_db, 'run')
    actions.resource_action(keystone_db_user, 'run')
    actions.resource_action(keystone_puppet, 'run')

    actions.resource_action(admin_tenant, 'run')
    actions.resource_action(admin_user, 'run')
    actions.resource_action(admin_role, 'run')

    actions.resource_action(keystone_service_endpoint, 'run')

    actions.resource_action(services_tenant, 'run')
    actions.resource_action(neutron_keystone_user, 'run')
    actions.resource_action(neutron_keystone_role, 'run')

    actions.resource_action(neutron_puppet, 'run')
    actions.resource_action(neutron_keystone_service_endpoint, 'run')

    # actions.resource_action(cinder_db, 'run')
    # actions.resource_action(cinder_db_user, 'run')
    # actions.resource_action(cinder_keystone_user, 'run')
    # actions.resource_action(cinder_keystone_role, 'run')

    # actions.resource_action(cinder_puppet, 'run')

    # actions.resource_action(nova_keystone_user, 'run')
    # actions.resource_action(nova_keystone_role, 'run')

    # actions.resource_action(nova_network_puppet, 'run')
    #actions.resource_action(nova_keystone_service_endpoint, 'run')

    time.sleep(10)


@click.command()
def undeploy():
    db = get_db()

    to_remove = [
        'neutron_keystone_service_endpoint',
        'neutron_puppet',
        'neutron_keystone_role',
        'neutron_keystone_user',
        'services_tenant',
        'keystone_service_endpoint',
        'admin_role',
        'admin_user',
        'admin_tenant',
        'keystone_puppet',
        'keystone_db_user',
        'keystone_db',
        'mariadb_service1',
        'openstack_rabbitmq_user',
        'openstack_vhost',
        'rabbitmq_service1',
    ]

    resources = map(resource.wrap_resource, db.get_list(collection=db.COLLECTIONS.resource))
    resources = {r.name: r for r in resources}

    for name in to_remove:
        actions.resource_action(resources[name], 'remove')

    #actions.resource_action(resources['nova_keystone_service_endpoint'], 'remove' )
    # actions.resource_action(resources['nova_network_puppet'], 'remove' )

    # actions.resource_action(resources['nova_keystone_role'], 'remove')
    # actions.resource_action(resources['nova_keystone_user'], 'remove')

    # actions.resource_action(resources['neutron_keystone_service_endpoint'], 'remove' )
    # actions.resource_action(resources['neutron_puppet'], 'remove' )

    # actions.resource_action(resources['cinder_puppet'], 'remove' )
    # actions.resource_action(resources['cinder_keystone_role'], 'remove')
    # actions.resource_action(resources['cinder_keystone_user'], 'remove')

    # actions.resource_action(resources['neutron_keystone_role'], 'remove')
    # actions.resource_action(resources['neutron_keystone_user'], 'remove')
    # actions.resource_action(resources['services_tenant'], 'remove')

    # actions.resource_action(resources['admin_role'], 'remove')
    # actions.resource_action(resources['admin_user'], 'remove')
    # actions.resource_action(resources['admin_tenant'], 'remove')

    # actions.resource_action(resources['keystone_puppet'], 'remove')
    # actions.resource_action(resources['keystone_db_user'], 'remove')
    # actions.resource_action(resources['keystone_db'], 'remove')

    # actions.resource_action(resources['mariadb_service1'], 'remove')

    # actions.resource_action(resources['openstack_rabbitmq_user'], 'remove')
    # actions.resource_action(resources['openstack_vhost'], 'remove')
    # actions.resource_action(resources['rabbitmq_service1'], 'remove')

    db.clear()

    signals.Connections.clear()


main.add_command(deploy)
main.add_command(undeploy)


if __name__ == '__main__':
    main()
