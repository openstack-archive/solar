import click
import json
import requests
import sys
import time

from solar.core import actions
from solar.core import resource
from solar.core import signals
from solar.core import validation

from solar.interfaces.db import get_db


@click.group()
def main():
    pass


@click.command()
def deploy():
    db = get_db()
    db.clear()

    signals.Connections.clear()

    node1 = resource.create('node1', 'resources/ro_node/', {'ip': '10.0.0.3', 'ssh_key': '/vagrant/.vagrant/machines/solar-dev1/virtualbox/private_key', 'ssh_user': 'vagrant'})
    node2 = resource.create('node2', 'resources/ro_node/', {'ip': '10.0.0.4', 'ssh_key': '/vagrant/.vagrant/machines/solar-dev2/virtualbox/private_key', 'ssh_user': 'vagrant'})

    rabbitmq_service1 = resource.create('rabbitmq_service1', 'resources/rabbitmq_service/', {'management_port': '15672', 'port': '5672', 'container_name': 'rabbitmq_service1', 'image': 'rabbitmq:3-management'})
    openstack_vhost = resource.create('openstack_vhost', 'resources/rabbitmq_vhost/', {'vhost_name': 'openstack'})
    openstack_rabbitmq_user = resource.create('openstack_rabbitmq_user', 'resources/rabbitmq_user/', {'user_name': 'openstack', 'password': 'openstack_password'})

    mariadb_service1 = resource.create('mariadb_service1', 'resources/mariadb_service', {'image': 'mariadb', 'root_password': 'mariadb', 'port': 3306})
    keystone_db = resource.create('keystone_db', 'resources/mariadb_keystone_db/', {'db_name': 'keystone_db', 'login_user': 'root'})
    keystone_db_user = resource.create('keystone_db_user', 'resources/mariadb_keystone_user/', {'new_user_name': 'keystone', 'new_user_password': 'keystone', 'login_user': 'root'})

    keystone_config1 = resource.create('keystone_config1', 'resources/keystone_config/', {'config_dir': '/etc/solar/keystone', 'admin_token': 'admin'})
    keystone_service1 = resource.create('keystone_service1', 'resources/keystone_service/', {'port': 5001, 'admin_port': 35357})

    keystone_config2 = resource.create('keystone_config2', 'resources/keystone_config/', {'config_dir': '/etc/solar/keystone', 'admin_token': 'admin'})
    keystone_service2 = resource.create('keystone_service2', 'resources/keystone_service/', {'port': 5002, 'admin_port': 35358})

    haproxy_keystone_config = resource.create('haproxy_keystone1_config', 'resources/haproxy_service_config/', {'name': 'keystone_config', 'listen_port': 5000, 'servers':[], 'ports':[]})
    haproxy_config = resource.create('haproxy_config', 'resources/haproxy_config', {'configs_names':[], 'configs_ports':[], 'listen_ports':[], 'configs':[]})
    haproxy_service = resource.create('haproxy_service', 'resources/docker_container/', {'image': 'tutum/haproxy', 'ports': [], 'host_binds': [], 'volume_binds':[]})

    glance_db = resource.create('glance_db', 'resources/mariadb_db/', {'db_name': 'glance_db', 'login_user': 'root'})
    glance_db_user = resource.create('glance_db_user', 'resources/mariadb_user/', {'new_user_name': 'glance', 'new_user_password': 'glance', 'login_user': 'root'})

    services_tenant = resource.create('glance_keystone_tenant', 'resources/keystone_tenant', {'tenant_name': 'services'})

    glance_keystone_user = resource.create('glance_keystone_user', 'resources/keystone_user', {'user_name': 'glance_admin', 'user_password': 'password1234', 'tenant_name': 'service_admins'})
    glance_keystone_role = resource.create('glance_keystone_role', 'resources/keystone_role', {'role_name': 'admin'})

    # TODO: add api_host and registry_host -- they can be different! Currently 'ip' is used.
    glance_config = resource.create('glance_config', 'resources/glance_config/', {'api_port': 9393})
    glance_api_container = resource.create('glance_api_container', 'resources/glance_api_service/', {'image': 'cgenie/centos-rdo-glance-api', 'ports': [{'value': [{'value': 9393}]}], 'host_binds': [], 'volume_binds': []})
    glance_registry_container = resource.create('glance_registry_container', 'resources/glance_registry_service/', {'image': 'cgenie/centos-rdo-glance-registry', 'ports': [{'value': [{'value': 9191}]}], 'host_binds': [], 'volume_binds': []})
    # TODO: admin_port should be refactored, we need to rethink docker
    # container resource and make it common for all
    # resources used in this demo
    glance_api_endpoint = resource.create('glance_api_endpoint', 'resources/keystone_service_endpoint/', {'adminurl': 'http://{{ip}}:{{admin_port}}', 'internalurl': 'http://{{ip}}:{{port}}', 'publicurl': 'http://{{ip}}:{{port}}', 'description': 'OpenStack Image Service', 'type': 'image'})
    # TODO: ports value 9393 is a HACK -- fix glance_api_container's port and move to some config
    # TODO: glance registry container's API port needs to point to haproxy_config
    haproxy_glance_api_config = resource.create('haproxy_glance_api_config', 'resources/haproxy_service_config/', {'name': 'glance_api_config', 'listen_port': 9292, 'servers': [], 'ports':[{'value': 9393}]})

    admin_tenant = resource.create('admin_tenant', 'resources/keystone_tenant', {'tenant_name': 'admin'})
    admin_user = resource.create('admin_user', 'resources/keystone_user', {'user_name': 'admin', 'user_password': 'admin'})
    admin_role = resource.create('admin_role', 'resources/keystone_role', {'role_name': 'admin'})
    keystone_service_endpoint = resource.create('keystone_service_endpoint', 'resources/keystone_service_endpoint/', {'adminurl': 'http://{{ip}}:{{admin_port}}/v2.0', 'internalurl': 'http://{{ip}}:{{port}}/v2.0', 'publicurl': 'http://{{ip}}:{{port}}/v2.0', 'description': 'OpenStack Identity Service', 'type': 'identity'})


    ####
    # connections
    ####

    # mariadb
    signals.connect(node1, mariadb_service1)

    # rabbitmq
    signals.connect(node1, rabbitmq_service1)
    signals.connect(rabbitmq_service1, openstack_vhost)
    signals.connect(rabbitmq_service1, openstack_rabbitmq_user)
    signals.connect(openstack_vhost, openstack_rabbitmq_user, {'vhost_name': 'vhost_name'})

    # keystone db
    signals.connect(node1, keystone_db)
    signals.connect(mariadb_service1, keystone_db, {'root_password': 'login_password', 'port': 'login_port'})

    # keystone_db_user
    signals.connect(node1, keystone_db_user)
    signals.connect(mariadb_service1, keystone_db_user, {'root_password': 'login_password', 'port': 'login_port'})
    signals.connect(keystone_db, keystone_db_user, {'db_name': 'db_name'})

    signals.connect(node1, keystone_config1)
    signals.connect(mariadb_service1, keystone_config1, {'ip': 'db_host', 'port': 'db_port'})
    signals.connect(keystone_db_user, keystone_config1, {'db_name': 'db_name', 'new_user_name': 'db_user', 'new_user_password': 'db_password'})

    signals.connect(node1, keystone_service1)
    signals.connect(keystone_config1, keystone_service1, {'config_dir': 'config_dir'})

    signals.connect(node2, keystone_config2)
    signals.connect(mariadb_service1, keystone_config2, {'ip': 'db_host', 'port': 'db_port'})
    signals.connect(keystone_db_user, keystone_config2, {'db_name': 'db_name', 'new_user_name': 'db_user', 'new_user_password': 'db_password'})

    signals.connect(node2, keystone_service2)
    signals.connect(keystone_config2, keystone_service2, {'config_dir': 'config_dir'})

    signals.connect(keystone_service1, haproxy_keystone_config, {'ip': 'servers', 'port': 'ports'})
    signals.connect(keystone_service2, haproxy_keystone_config, {'ip': 'servers', 'port': 'ports'})

    signals.connect(node2, haproxy_config)
    signals.connect(haproxy_keystone_config, haproxy_config, {'listen_port': 'listen_ports', 'name': 'configs_names', 'ports': 'configs_ports', 'servers': 'configs'})

    signals.connect(node2, haproxy_service)
    signals.connect(haproxy_config, haproxy_service, {'listen_ports': 'ports', 'config_dir': 'host_binds'})

    # keystone configuration
    signals.connect(keystone_config1, admin_tenant)
    signals.connect(keystone_service1, admin_tenant, {'admin_port': 'keystone_port', 'ip': 'keystone_host'})
    signals.connect(admin_tenant, admin_user)
    signals.connect(admin_user, admin_role)
    signals.connect(keystone_config1, keystone_service_endpoint)
    signals.connect(keystone_service1, keystone_service_endpoint, {'ip': 'keystone_host','admin_port': 'admin_port', 'port': 'port'})
    signals.connect(keystone_service1, keystone_service_endpoint, {'admin_port': 'keystone_port'})

    # glance db
    signals.connect(node1, glance_db)
    signals.connect(mariadb_service1, glance_db, {'root_password': 'login_password', 'port': 'login_port'})
    signals.connect(node1, glance_db_user)
    signals.connect(mariadb_service1, glance_db_user, {'root_password': 'login_password', 'port': 'login_port'})
    signals.connect(glance_db, glance_db_user, {'db_name': 'db_name'})

    # glance keystone user
    signals.connect(keystone_config1, services_tenant)
    signals.connect(keystone_service1, services_tenant, {'admin_port': 'keystone_port', 'ip': 'keystone_host'})
    signals.connect(services_tenant, glance_keystone_user)  # standard ip, ssh_key, ssh_user
    signals.connect(glance_keystone_user, glance_keystone_role)
    signals.connect(keystone_service1, glance_keystone_user, {'admin_port': 'keystone_port', 'ip': 'keystone_host'})
    signals.connect(keystone_config1, glance_keystone_user, {'admin_token': 'admin_token'})
    signals.connect(glance_keystone_user, glance_config, {'user_name': 'keystone_admin_user', 'user_password': 'keystone_admin_password', 'tenant_name': 'keystone_admin_tenant'})
    signals.connect(keystone_service2, glance_config, {'admin_port': 'keystone_admin_port'})

    # glance
    signals.connect(node2, glance_config)
    signals.connect(haproxy_keystone_config, glance_config, {'listen_port': 'keystone_port'})
    signals.connect(haproxy_service, glance_config, {'ip': 'keystone_ip'})
    signals.connect(mariadb_service1, glance_config, {'ip': 'mysql_ip'})
    signals.connect(glance_db, glance_config, {'db_name': 'mysql_db'})
    signals.connect(glance_db_user, glance_config, {'new_user_name': 'mysql_user', 'new_user_password': 'mysql_password'})
    signals.connect(node2, glance_api_container)
    signals.connect(glance_config, glance_api_container, {'config_dir': 'host_binds'})

    signals.connect(glance_db_user, glance_api_container, {'new_user_password': 'db_password'})
    signals.connect(glance_keystone_user, glance_api_container, {'user_password': 'keystone_password'})
    signals.connect(glance_keystone_user, glance_api_container, {'admin_token': 'keystone_admin_token'})
    signals.connect(haproxy_config, glance_api_container, {'ip': 'keystone_host'})

    signals.connect(node2, glance_registry_container)
    signals.connect(glance_config, glance_registry_container, {'config_dir': 'host_binds'})

    signals.connect(mariadb_service1, glance_registry_container, {'ip': 'db_host'})
    signals.connect(glance_db, glance_registry_container, {'db_name': 'db_name', 'login_password': 'db_root_password'})
    signals.connect(glance_db_user, glance_registry_container, {'new_user_name': 'db_user', 'new_user_password': 'db_password'})
    signals.connect(glance_keystone_user, glance_registry_container, {'tenant_name': 'keystone_admin_tenant', 'user_name': 'keystone_user', 'user_password': 'keystone_password'})
    signals.connect(glance_keystone_user, glance_registry_container, {'admin_token': 'keystone_admin_token'})
    signals.connect(haproxy_config, glance_registry_container, {'ip': 'keystone_host'})

    # glance haproxy
    signals.connect(glance_api_container, haproxy_glance_api_config, {'ip': 'servers'})
    #signals.connect(glance_config, haproxy_glance_api_config, {'api_port': 'ports'})
    signals.connect(haproxy_glance_api_config, haproxy_config, {'listen_port': 'listen_ports', 'name': 'configs_names', 'ports': 'configs_ports', 'servers': 'configs'})

    # glance keystone endpoint
    #signals.connect(glance_api_container, glance_api_endpoint, {'ip': 'ip', 'ssh_user': 'ssh_user', 'ssh_key': 'ssh_key'})
    signals.connect(haproxy_service, glance_api_endpoint, {'ip': 'ip', 'ssh_user': 'ssh_user', 'ssh_key': 'ssh_key'})
    signals.connect(keystone_config1, glance_api_endpoint, {'admin_token': 'admin_token'})
    signals.connect(keystone_service1, glance_api_endpoint, {'ip': 'keystone_host', 'admin_port': 'keystone_port'})
    signals.connect(haproxy_glance_api_config, glance_api_endpoint, {'listen_port': 'admin_port'})
    signals.connect(haproxy_glance_api_config, glance_api_endpoint, {'listen_port': 'port'})


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
    actions.resource_action(mariadb_service1, 'run')
    actions.resource_action(rabbitmq_service1, 'run')
    actions.resource_action(openstack_vhost, 'run')
    actions.resource_action(openstack_rabbitmq_user, 'run')
    actions.resource_action(keystone_db, 'run')
    actions.resource_action(keystone_db_user, 'run')
    actions.resource_action(keystone_config1, 'run')
    actions.resource_action(keystone_service1, 'run')
    actions.resource_action(keystone_config2, 'run')
    actions.resource_action(keystone_service2, 'run')

    actions.resource_action(haproxy_config, 'run')
    actions.resource_action(haproxy_service, 'run')

    actions.resource_action(admin_tenant, 'run')
    actions.resource_action(admin_user, 'run')
    actions.resource_action(admin_role, 'run')
    actions.resource_action(keystone_service_endpoint, 'run')

    actions.resource_action(services_tenant, 'run')
    actions.resource_action(glance_keystone_user, 'run')
    actions.resource_action(glance_keystone_role, 'run')
    actions.resource_action(glance_db, 'run')
    actions.resource_action(glance_db_user, 'run')
    actions.resource_action(glance_config, 'run')
    actions.resource_action(glance_api_container, 'run')
    time.sleep(10) #TODO fix
    actions.resource_action(glance_api_endpoint, 'run')
    actions.resource_action(glance_registry_container, 'run')
    time.sleep(10)

    # HAProxy needs to be restarted after Glance API is up
    actions.resource_action(haproxy_service, 'remove')
    actions.resource_action(haproxy_service, 'run')
    time.sleep(10)

    # test working configuration
    requests.get('http://%s:%s' % (keystone_service1.args['ip'].value, keystone_service1.args['port'].value))
    requests.get('http://%s:%s' % (keystone_service2.args['ip'].value, keystone_service2.args['port'].value))
    requests.get('http://%s:%s' % (haproxy_service.args['ip'].value, haproxy_service.args['ports'].value[0]['value'][0]['value']))

    token_data = requests.post(
        'http://%s:%s/v2.0/tokens' % (haproxy_service.args['ip'].value, haproxy_keystone_config.args['listen_port'].value),
        json.dumps({
            'auth': {
                'tenantName': glance_keystone_user.args['tenant_name'].value,
                'passwordCredentials': {
                    'username': glance_keystone_user.args['user_name'].value,
                    'password': glance_keystone_user.args['user_password'].value,
                }
            }
        }),
        headers={'Content-Type': 'application/json'}
    )

    token = token_data.json()['access']['token']['id']
    print 'TOKEN: {}'.format(token)

    requests.get('http://%s:%s' % (rabbitmq_service1.args['ip'].value, rabbitmq_service1.args['management_port'].value))

    images = requests.get(
        'http://%s:%s/v1/images' % (glance_api_container.args['ip'].value, haproxy_glance_api_config.args['listen_port'].value),
        headers={'X-Auth-Token': token}
    )
    assert images.json() == {'images': []}
    images = requests.get(
        'http://%s:%s' % (glance_registry_container.args['ip'].value, glance_registry_container.args['ports'].value[0]['value'][0]['value']),
        headers={'X-Auth-Token': token}
    )
    assert images.json() == {'images': []}


@click.command()
def undeploy():
    db = get_db()

    resources = map(resource.wrap_resource, db.get_list(collection=db.COLLECTIONS.resource))
    resources = {r.name: r for r in resources}

    actions.resource_action(resources['glance_api_endpoint'], 'remove')
    actions.resource_action(resources['glance_api_container'], 'remove')
    actions.resource_action(resources['glance_registry_container'], 'remove')
    actions.resource_action(resources['glance_config'], 'remove')
    actions.resource_action(resources['glance_db_user'], 'remove')
    actions.resource_action(resources['glance_db'], 'remove')
    actions.resource_action(resources['glance_keystone_role'], 'remove')
    actions.resource_action(resources['glance_keystone_user'], 'remove')
    actions.resource_action(resources['glance_keystone_tenant'], 'remove')

    actions.resource_action(resources['keystone_service_endpoint'], 'remove')
    actions.resource_action(resources['admin_role'], 'remove')
    actions.resource_action(resources['admin_user'], 'remove')
    actions.resource_action(resources['admin_tenant'], 'remove')

    actions.resource_action(resources['haproxy_service'], 'remove')
    actions.resource_action(resources['haproxy_config'], 'remove')
    actions.resource_action(resources['keystone_service2'], 'remove')
    actions.resource_action(resources['keystone_config2'], 'remove')
    actions.resource_action(resources['keystone_service1'], 'remove')
    actions.resource_action(resources['keystone_config1'], 'remove')
    actions.resource_action(resources['keystone_db_user'], 'remove')
    actions.resource_action(resources['keystone_db'], 'remove')
    actions.resource_action(resources['mariadb_service1'], 'remove')
    actions.resource_action(resources['openstack_rabbitmq_user'], 'remove')
    actions.resource_action(resources['openstack_vhost'], 'remove')
    actions.resource_action(resources['rabbitmq_service1'], 'remove')

    db.clear()

    signals.Connections.clear()


main.add_command(deploy)
main.add_command(undeploy)


if __name__ == '__main__':
    main()
