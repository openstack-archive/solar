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

    node1 = resource.create('node1', 'resources/ro_node/', {'ip': '10.0.0.3', 'ssh_key': '/vagrant/.vagrant/machines/solar-dev2/virtualbox/private_key', 'ssh_user': 'vagrant'})
    node2 = resource.create('node2', 'resources/ro_node/', {'ip': '10.0.0.4', 'ssh_key': '/vagrant/.vagrant/machines/solar-dev3/virtualbox/private_key', 'ssh_user': 'vagrant'})
    node3 = resource.create('node3', 'resources/ro_node/', {'ip':'10.0.0.5', 'ssh_key' : '/vagrant/.vagrant/machines/solar-dev4/virtualbox/private_key', 'ssh_user':'vagrant'})

    mariadb_service1 = resource.create('mariadb_service1', 'resources/mariadb_service', {'image': 'mariadb', 'root_password': 'mariadb', 'port': 3306, 'ip': '', 'ssh_user': '', 'ssh_key': ''})
    keystone_db = resource.create('keystone_db', 'resources/mariadb_db/', {'db_name': 'keystone_db', 'login_password': '', 'login_user': 'root', 'login_port': '', 'ip': '', 'ssh_user': '', 'ssh_key': ''})
    keystone_db_user = resource.create('keystone_db_user', 'resources/mariadb_user/', {'new_user_name': 'keystone', 'new_user_password': 'keystone', 'db_name': '', 'login_password': '', 'login_user': 'root', 'login_port': '', 'ip': '', 'ssh_user': '', 'ssh_key': ''})

    keystone_config1 = resource.create('keystone_config1', 'resources/keystone_config/', {'config_dir': '/etc/solar/keystone', 'ip': '', 'ssh_user': '', 'ssh_key': '', 'admin_token': 'admin', 'db_password': '', 'db_name': '', 'db_user': '', 'db_host': '', 'db_port': ''})
    keystone_service1 = resource.create('keystone_service1', 'resources/keystone_service/', {'port': 5001, 'admin_port': 35357, 'image': '', 'ip': '', 'ssh_key': '', 'ssh_user': '', 'config_dir': ''})

    keystone_config2 = resource.create('keystone_config2', 'resources/keystone_config/', {'config_dir': '/etc/solar/keystone', 'ip': '', 'ssh_user': '', 'ssh_key': '', 'admin_token': 'admin', 'db_password': '', 'db_name': '', 'db_user': '', 'db_host': '', 'db_port': ''})
    keystone_service2 = resource.create('keystone_service2', 'resources/keystone_service/', {'port': 5002, 'admin_port': 35357, 'image': '', 'ip': '', 'ssh_key': '', 'ssh_user': '', 'config_dir': ''})

    haproxy_keystone_config = resource.create('haproxy_keystone1_config', 'resources/haproxy_keystone_config/', {'name': 'keystone_config', 'listen_port':5000, 'servers':[], 'ports':[]})
    haproxy_config = resource.create('haproxy_config', 'resources/haproxy', {'ip': '', 'ssh_key': '', 'ssh_user': '', 'configs_names':[], 'configs_ports':[], 'listen_ports':[], 'configs':[], 'config_dir': ''})
    haproxy_service = resource.create('haproxy_service', 'resources/docker_container/', {'image': 'tutum/haproxy', 'ports': [], 'host_binds': [], 'volume_binds':[], 'ip': '', 'ssh_key': '', 'ssh_user': ''})

    glance_db = resource.create('glance_db', 'resources/mariadb_db/', {'db_name':'glance_db', 'login_password':'', 'login_user':'root', 'login_port': '', 'ip':'', 'ssh_user':'', 'ssh_key':''})
    glance_db_user = resource.create('glance_db_user', 'resources/mariadb_user/', {'new_user_name' : 'glance', 'new_user_password' : 'glance', 'db_name':'', 'login_password':'', 'login_user':'root', 'login_port': '', 'ip':'', 'ssh_user':'', 'ssh_key':''})

    glance_config = resource.create('glance_config', 'resources/glance_config/', {'ip': '', 'ssh_key': '', 'ssh_user': '', 'keystone_ip': '', 'keystone_port': '', 'config_dir': {}, 'api_port': '', 'registry_port': '', 'mysql_ip': '', 'mysql_db': '', 'mysql_user': '', 'mysql_password': '', 'keystone_admin_user': '', 'keystone_admin_password': '', 'keystone_admin_tenant': ''})
    glance_container = resource.create('glance_container', 'resources/docker_container/', {'image' : 'krystism/openstack-glance', 'ports': [{'value': [{'value': 9191}, {'value': 9292}]}], 'host_binds': [], 'volume_binds':[], 'ip':'', 'ssh_key':'', 'ssh_user':''})


    ####
    # connections
    ####

    # mariadb
    signals.connect(node1, mariadb_service1)

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

    # glance
    signals.connect(node1, glance_db)
    signals.connect(mariadb_service1, glance_db, {'root_password':'login_password', 'port':'login_port'})
    signals.connect(node1, glance_db_user)
    signals.connect(mariadb_service1, glance_db_user, {'root_password':'login_password', 'port':'login_port'})
    signals.connect(glance_db, glance_db_user, {'db_name':'db_name'})

    signals.connect(node3, glance_config)
    signals.connect(haproxy_keystone_config, glance_config, {'listen_port': 'keystone_port'})
    signals.connect(haproxy_service, glance_config, {'ip': 'keystone_ip'})
    signals.connect(mariadb_service1, glance_config, {'ip': 'mysql_ip'})
    signals.connect(glance_db, glance_config, {'db_name': 'mysql_db'})
    signals.connect(glance_db_user, glance_config, {'new_user_name': 'mysql_user', 'new_user_password': 'mysql_password'})
    signals.connect(node3, glance_container)
    signals.connect(glance_config, glance_container, {'config_dir': 'host_binds'})


    has_errors = False
    for r in [node1,
              node2,
              mariadb_service1,
              keystone_db,
              keystone_db_user,
              keystone_config1,
              keystone_service1,
              keystone_config2,
              keystone_service2,
              haproxy_keystone_config,
              haproxy_config,
              haproxy_service,
              glance_config,
              glance_db,
              glance_db_user,
              glance_container]:
        errors = validation.validate_resource(r)
        if errors:
            has_errors = True
            print 'ERROR: %s: %s' % (r.name, errors)

    if has_errors:
        sys.exit(1)


    # run
    actions.resource_action(mariadb_service1, 'run')
    time.sleep(10)
    actions.resource_action(keystone_db, 'run')
    actions.resource_action(keystone_db_user, 'run')
    actions.resource_action(keystone_config1, 'run')
    actions.resource_action(keystone_service1, 'run')
    actions.resource_action(keystone_config2, 'run')
    actions.resource_action(keystone_service2, 'run')
    actions.resource_action(haproxy_config, 'run')
    actions.resource_action(haproxy_service, 'run')
    actions.resource_action(glance_db, 'run')
    actions.resource_action(glance_db_user, 'run')
    actions.resource_action(glance_config, 'run')
    actions.resource_action(glance_container, 'run')
    time.sleep(10)


    # test working configuration
    requests.get('http://%s:%s' % (keystone_service1.args['ip'].value, keystone_service1.args['port'].value))
    requests.get('http://%s:%s' % (keystone_service2.args['ip'].value, keystone_service2.args['port'].value))
    requests.get('http://%s:%s' % (haproxy_service.args['ip'].value, haproxy_service.args['ports'].value[0]['value'][0]['value']))
    requests.get('http://%s:%s' % (glance_container.args['ip'].value, glance_container.args['ports'].value[0]['value'][0]['value']))
    requests.get('http://%s:%s' % (glance_container.args['ip'].value, glance_container.args['ports'].value[0]['value'][1]['value']))




@click.command()
def undeploy():
    db = get_db()

    resources = map(resource.wrap_resource, db.get_list('resource'))
    resources = {r.name: r for r in resources}

    actions.resource_action(resources['glance_container'], 'run')
    actions.resource_action(resources['glance_config'], 'run')
    actions.resource_action(resources['glance_db_user'], 'run')
    actions.resource_action(resources['glance_db'], 'run')
    actions.resource_action(resources['haproxy_service'], 'remove')
    actions.resource_action(resources['haproxy_config'], 'remove')
    actions.resource_action(resources['keystone_service2'], 'remove')
    actions.resource_action(resources['keystone_config2'], 'remove')
    actions.resource_action(resources['keystone_service1'], 'remove')
    actions.resource_action(resources['keystone_config1'], 'remove')
    actions.resource_action(resources['keystone_db_user'], 'remove')
    actions.resource_action(resources['keystone_db'], 'remove')
    actions.resource_action(resources['mariadb_service1'], 'remove')

    db.clear()

    signals.Connections.clear()


main.add_command(deploy)
main.add_command(undeploy)


if __name__ == '__main__':
    main()
