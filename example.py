import shutil
import os

from solar.core import resource
from solar.core import signals


signals.Connections.clear()

if os.path.exists('rs'):
    shutil.rmtree('rs')
os.mkdir('rs')

node1 = resource.create('node1', 'resources/ro_node/', 'rs/', {'ip':'10.0.0.3', 'ssh_key' : '/vagrant/tmp/keys/ssh_private', 'ssh_user':'vagrant'})
node2 = resource.create('node2', 'resources/ro_node/', 'rs/', {'ip':'10.0.0.4', 'ssh_key' : '/vagrant/tmp/keys/ssh_private', 'ssh_user':'vagrant'})
node3 = resource.create('node3', 'resources/ro_node/', 'rs/', {'ip':'10.0.0.5', 'ssh_key' : '/vagrant/tmp/keys/ssh_private', 'ssh_user':'vagrant'})

mariadb_service1 = resource.create('mariadb_service1', 'resources/mariadb_service', 'rs/', {'image':'mariadb', 'root_password' : 'mariadb', 'port' : '3306', 'ip': '', 'ssh_user': '', 'ssh_key': ''})
keystone_db = resource.create('keystone_db', 'resources/mariadb_db/', 'rs/', {'db_name':'keystone_db', 'login_password':'', 'login_user':'root', 'login_port': '', 'ip':'', 'ssh_user':'', 'ssh_key':''})
keystone_db_user = resource.create('keystone_db_user', 'resources/mariadb_user/', 'rs/', {'new_user_name' : 'keystone', 'new_user_password' : 'keystone', 'db_name':'', 'login_password':'', 'login_user':'root', 'login_port': '', 'ip':'', 'ssh_user':'', 'ssh_key':''})

keystone_config1 = resource.create('keystone_config1', 'resources/keystone_config/', 'rs/', {'config_dir' : '/etc/solar/keystone', 'ip':'', 'ssh_user':'', 'ssh_key':'', 'admin_token':'admin', 'db_password':'', 'db_name':'', 'db_user':'', 'db_host':''})
keystone_service1 = resource.create('keystone_service1', 'resources/keystone_service/', 'rs/', {'port':'5000', 'admin_port':'35357', 'ip':'', 'ssh_key':'', 'ssh_user':'', 'config_dir':'', 'config_dir':''})

keystone_config2 = resource.create('keystone_config2', 'resources/keystone_config/', 'rs/', {'config_dir' : '/etc/solar/keystone', 'ip':'', 'ssh_user':'', 'ssh_key':'', 'admin_token':'admin', 'db_password':'', 'db_name':'', 'db_user':'', 'db_host':''})
keystone_service2 = resource.create('keystone_service2', 'resources/keystone_service/', 'rs/', {'port':'5000', 'admin_port':'35357', 'ip':'', 'ssh_key':'', 'ssh_user':'', 'config_dir':'', 'config_dir':''})


haproxy_keystone_config = resource.create('haproxy_keystone1_config', 'resources/haproxy_config/', 'rs/', {'name':'keystone_config', 'listen_port':'5000', 'servers':[], 'ports':[]})
haproxy_config = resource.create('haproxy_config', 'resources/haproxy', 'rs/', {'ip':'', 'ssh_key':'', 'ssh_user':'', 'configs_names':[], 'configs_ports':[], 'listen_ports':[], 'configs':[]})
haproxy_service = resource.create('haproxy_service', 'resources/docker_container/', 'rs/', {'image' : 'tutum/haproxy', 'ports': [], 'host_binds': [], 'volume_binds':[], 'ip':'', 'ssh_key':'', 'ssh_user':''})


####
# connections
####

#mariadb
signals.connect(node1, mariadb_service1)

#keystone db
signals.connect(node1, keystone_db)
signals.connect(mariadb_service1, keystone_db, {'root_password':'login_password', 'port':'login_port'})

# keystone_db_user
signals.connect(node1, keystone_db_user)
signals.connect(mariadb_service1, keystone_db_user, {'root_password':'login_password', 'port':'login_port'})
signals.connect(keystone_db, keystone_db_user, {'db_name':'db_name'})

signals.connect(node1, keystone_config1)
signals.connect(mariadb_service1, keystone_config1, {'ip':'db_host'})
signals.connect(keystone_db_user, keystone_config1, {'db_name':'db_name', 'new_user_name':'db_user', 'new_user_password':'db_password'})

signals.connect(node1, keystone_service1)
signals.connect(keystone_config1, keystone_service1, {'config_dir': 'config_dir'})

signals.connect(node2, keystone_config2)
signals.connect(mariadb_service1, keystone_config2, {'ip':'db_host'})
signals.connect(keystone_db_user, keystone_config2, {'db_name':'db_name', 'new_user_name':'db_user', 'new_user_password':'db_password'})

signals.connect(node2, keystone_service2)
signals.connect(keystone_config2, keystone_service2, {'config_dir': 'config_dir'})

signals.connect(keystone_service1, haproxy_keystone_config, {'ip':'servers', 'port':'ports'})

signals.connect(node1, haproxy_config)
signals.connect(haproxy_keystone_config, haproxy_config, {'listen_port': 'listen_ports', 'name':'configs_names', 'ports' : 'configs_ports', 'servers':'configs'})

signals.connect(node1, haproxy_service)
signals.connect(haproxy_config, haproxy_service, {'listen_ports':'ports', 'config_dir':'host_binds'})


#run
from solar.core import actions

actions.resource_action(mariadb_service1, 'run')
actions.resource_action(keystone_db, 'run')
actions.resource_action(keystone_db_user, 'run')
actions.resource_action(keystone_config1, 'run')
actions.resource_action(keystone_service1, 'run')
actions.resource_action(haproxy_config, 'run')
actions.resource_action(haproxy_service, 'run')


#remove
actions.resource_action(haproxy_service, 'remove')
actions.resource_action(haproxy_config, 'remove')
actions.resource_action(keystone_service1, 'remove')
actions.resource_action(keystone_config1, 'remove')
actions.resource_action(keystone_db_user, 'remove')
actions.resource_action(keystone_db, 'remove')
actions.resource_action(mariadb_service1, 'remove')
