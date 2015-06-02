import click
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

    rabbitmq_service1 = resource.create('rabbitmq_service1', 'resources/rabbitmq_service/', {'ssh_user':'', 'ip':'','management_port':'15672', 'port':'5672', 'ssh_key':'', 'container_name': 'rabbitmq_service1', 'image': 'rabbitmq:3-management'})
    openstack_vhost = resource.create('openstack_vhost', 'resources/rabbitmq_vhost/', {'ssh_user':'', 'ip':'', 'ssh_key':'', 'vhost_name' : 'openstack', 'container_name':''})
    openstack_rabbitmq_user = resource.create('openstack_rabbitmq_user', 'resources/rabbitmq_user/', {'ssh_user':'', 'ip':'', 'ssh_key':'', 'vhost_name' : '', 'user_name':'openstack', 'password':'openstack_password', 'container_name':''})

    mariadb_service1 = resource.create('mariadb_service1', 'resources/mariadb_service', {'image': 'mariadb', 'root_password': 'mariadb', 'port': 3306, 'ip': '', 'ssh_user': '', 'ssh_key': ''})
    keystone_db = resource.create('keystone_db', 'resources/mariadb_keystone_db/', {'db_name': 'keystone_db', 'login_password': '', 'login_user': 'root', 'login_port': '', 'ip': '', 'ssh_user': '', 'ssh_key': ''})
    keystone_db_user = resource.create('keystone_db_user', 'resources/mariadb_keystone_user/', {'new_user_name': 'keystone', 'new_user_password': 'keystone', 'db_name': '', 'login_password': '', 'login_user': 'root', 'login_port': '', 'ip': '', 'ssh_user': '', 'ssh_key': ''})

    keystone_config1 = resource.create('keystone_config1', 'resources/keystone_config/', {'config_dir': '/etc/solar/keystone', 'ip': '', 'ssh_user': '', 'ssh_key': '', 'admin_token': 'admin', 'db_password': '', 'db_name': '', 'db_user': '', 'db_host': '', 'db_port': ''})
    keystone_service1 = resource.create('keystone_service1', 'resources/keystone_service/', {'port': 5001, 'admin_port': 35357, 'image': '', 'ip': '', 'ssh_key': '', 'ssh_user': '', 'config_dir': ''})

    keystone_config2 = resource.create('keystone_config2', 'resources/keystone_config/', {'config_dir': '/etc/solar/keystone', 'ip': '', 'ssh_user': '', 'ssh_key': '', 'admin_token': 'admin', 'db_password': '', 'db_name': '', 'db_user': '', 'db_host': '', 'db_port': ''})
    keystone_service2 = resource.create('keystone_service2', 'resources/keystone_service/', {'port': 5002, 'admin_port': 35358, 'image': '', 'ip': '', 'ssh_key': '', 'ssh_user': '', 'config_dir': ''})

    haproxy_keystone_config = resource.create('haproxy_keystone1_config', 'resources/haproxy_keystone_config/', {'name': 'keystone_config', 'listen_port':5000, 'servers':[], 'ports':[]})
    haproxy_config = resource.create('haproxy_config', 'resources/haproxy_config', {'ip': '', 'ssh_key': '', 'ssh_user': '', 'configs_names':[], 'configs_ports':[], 'listen_ports':[], 'configs':[], 'config_dir': ''})
    haproxy_service = resource.create('haproxy_service', 'resources/docker_container/', {'image': 'tutum/haproxy', 'ports': [], 'host_binds': [], 'volume_binds':[], 'ip': '', 'ssh_key': '', 'ssh_user': ''})

    admin_tenant = resource.create('admin_tenant', 'resources/keystone_tenant', {'keystone_host': '', 'keystone_port':'', 'login_user': 'admin', 'admin_token':'', 'tenant_name' : 'admin', 'ip': '', 'ssh_user': '', 'ssh_key': ''})
    admin_user = resource.create('admin_user', 'resources/keystone_user', {'keystone_host': '', 'keystone_port':'', 'login_user': 'admin', 'admin_token':'', 'tenant_name' : '', 'user_name': 'admin', 'user_password':'admin', 'ip': '', 'ssh_user': '', 'ssh_key': ''})
    admin_role = resource.create('admin_role', 'resources/keystone_role', {'keystone_host': '', 'keystone_port':'', 'login_user': 'admin', 'admin_token':'', 'tenant_name' : '', 'user_name': '', 'role_name': 'admin', 'ip': '', 'ssh_user': '', 'ssh_key': ''})
    keystone_service_endpoint = resource.create('keystone_service_endpoint', 'resources/keystone_service_endpoint/', {'ip':'', 'ssh_key' : '', 'ssh_user':'', 'admin_port':'', 'admin_token':'', 'adminurl':'http://{{ip}}:{{admin_port}}/v2.0', 'internalurl':'http://{{ip}}:{{port}}/v2.0', 'publicurl':'http://{{ip}}:{{port}}/v2.0', 'description':'OpenStack Identity Service', 'keystone_host':'', 'keystone_port':'', 'name':'keystone', 'port':'', 'type':'identity'})


    ####
    # connections
    ####

    # mariadb
    signals.connect(node1, mariadb_service1)

    #rabbitmq
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

    #keystone configuration
    signals.connect(keystone_config1, admin_tenant)
    signals.connect(keystone_service1, admin_tenant, {'admin_port': 'keystone_port', 'ip': 'keystone_host'})
    signals.connect(admin_tenant, admin_user)
    signals.connect(admin_user, admin_role)
    signals.connect(keystone_config1, keystone_service_endpoint)
    signals.connect(keystone_service1, keystone_service_endpoint, {'ip': 'keystone_host','admin_port':'admin_port', 'port':'port'})
    signals.connect(keystone_service1, keystone_service_endpoint, {'admin_port': 'keystone_port'})


    has_errors = False
    for r in [node1,
              node2,
              mariadb_service1,
              keystone_db,
              rabbitmq_service1,
              openstack_vhost,
              openstack_rabbitmq_user,
              keystone_db_user,
              keystone_config1,
              keystone_service1,
              keystone_config2,
              keystone_service2,
              haproxy_keystone_config,
              haproxy_config,
              haproxy_service,
              admin_tenant,
              admin_user,
              admin_role,
              keystone_service_endpoint]:
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
    time.sleep(10) #TODO fix keystone services to check if tables are created
    actions.resource_action(keystone_config2, 'run')
    actions.resource_action(keystone_service2, 'run')
    actions.resource_action(haproxy_config, 'run')
    actions.resource_action(haproxy_service, 'run')
    time.sleep(10) #TODO fix haproxy to wait until it's ready

    actions.resource_action(admin_tenant, 'run')
    actions.resource_action(admin_user, 'run')
    actions.resource_action(admin_role, 'run')
    actions.resource_action(keystone_service_endpoint, 'run')

    # test working configuration
    requests.get('http://%s:%s' % (keystone_service1.args['ip'].value, keystone_service1.args['port'].value))
    requests.get('http://%s:%s' % (keystone_service2.args['ip'].value, keystone_service2.args['port'].value))
    requests.get('http://%s:%s' % (haproxy_service.args['ip'].value, haproxy_service.args['ports'].value[0]['value'][0]['value']))
    requests.get('http://%s:%s' % (rabbitmq_service1.args['ip'].value, rabbitmq_service1.args['management_port'].value))


@click.command()
def undeploy():
    db = get_db()

    resources = map(resource.wrap_resource, db.get_list('resource'))
    resources = {r.name: r for r in resources}

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
