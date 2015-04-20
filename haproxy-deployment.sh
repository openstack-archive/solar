#!/usr/bin/env bash
# HAProxy deployment with Keystone and Nova

set -e

cd /vagrant

rm clients.json
rm -Rf rs/*

# Create resources
python cli.py resource create node1 x/resources/ro_node/ rs/ '{"ip":"10.0.0.3", "ssh_key" : "/vagrant/tmp/keys/ssh_private", "ssh_user":"vagrant"}'
python cli.py resource create node2 x/resources/ro_node/ rs/ '{"ip":"10.0.0.4", "ssh_key" : "/vagrant/tmp/keys/ssh_private", "ssh_user":"vagrant"}'
python cli.py resource create node3 x/resources/ro_node/ rs/ '{"ip":"10.0.0.5", "ssh_key" : "/vagrant/tmp/keys/ssh_private", "ssh_user":"vagrant"}'
python cli.py resource create node4 x/resources/ro_node/ rs/ '{"ip":"10.0.0.6", "ssh_key" : "/vagrant/tmp/keys/ssh_private", "ssh_user":"vagrant"}'
python cli.py resource create node5 x/resources/ro_node/ rs/ '{"ip":"10.0.0.7", "ssh_key" : "/vagrant/tmp/keys/ssh_private", "ssh_user":"vagrant"}'

python cli.py resource create mariadb_keystone1_data x/resources/data_container/ rs/ '{"image": "mariadb", "export_volumes" : ["/var/lib/mysql"], "ip": "", "ssh_user": "", "ssh_key": ""}'
python cli.py resource create mariadb_keystone2_data x/resources/data_container/ rs/ '{"image": "mariadb", "export_volumes" : ["/var/lib/mysql"], "ip": "", "ssh_user": "", "ssh_key": ""}'
python cli.py resource create keystone1 x/resources/keystone/ rs/ '{"ip": "", "ssh_user": "", "ssh_key": ""}'
python cli.py resource create keystone2 x/resources/keystone/ rs/ '{"ip": "", "ssh_user": "", "ssh_key": ""}'
python cli.py resource create haproxy_keystone_config x/resources/haproxy_config/ rs/ '{"servers": {}, "ssh_user": "", "ssh_key": ""}'

python cli.py resource create mariadb_nova1_data x/resources/data_container/ rs/ '{"image" : "mariadb", "export_volumes" : ["/var/lib/mysql"], "ip": "", "ssh_user": "", "ssh_key": ""}'
python cli.py resource create mariadb_nova2_data x/resources/data_container/ rs/ '{"image" : "mariadb", "export_volumes" : ["/var/lib/mysql"], "ip": "", "ssh_user": "", "ssh_key": ""}'
python cli.py resource create nova1 x/resources/nova/ rs/ '{"server": "", "ssh_user": "", "ssh_key": ""}'
python cli.py resource create nova2 x/resources/nova/ rs/ '{"server": "", "ssh_user": "", "ssh_key": ""}'
python cli.py resource create haproxy_nova_config x/resources/haproxy_config/ rs/ '{"servers": {}, "ssh_user": "", "ssh_key": ""}'

python cli.py resource create haproxy x/resources/haproxy/ rs/ '{"configs": {}, "ssh_user": "", "ssh_key": ""}'


# Connect resources
python cli.py connect rs/node1 rs/mariadb_keystone1_data
python cli.py connect rs/node2 rs/mariadb_keystone2_data
python cli.py connect rs/mariadb_keystone1_data rs/keystone1
python cli.py connect rs/mariadb_keystone2_data rs/keystone2
python cli.py connect rs/keystone1 rs/haproxy_keystone_config --mapping '{"ip": "servers"}'
python cli.py connect rs/keystone2 rs/haproxy_keystone_config --mapping '{"ip": "servers"}'

python cli.py connect rs/node3 rs/mariadb_nova1_data
python cli.py connect rs/node4 rs/mariadb_nova2_data
python cli.py connect rs/mariadb_nova1_data rs/nova1
python cli.py connect rs/mariadb_nova2_data rs/nova2
python cli.py connect rs/nova1 rs/haproxy_nova_config --mapping '{"ip": "servers"}'
python cli.py connect rs/nova2 rs/haproxy_nova_config --mapping '{"ip": "servers"}'

python cli.py connect rs/node5 rs/haproxy
python cli.py connect rs/haproxy_keystone_config rs/haproxy --mapping '{"server": "configs"}'
python cli.py connect rs/haproxy_nova_config rs/haproxy --mapping '{"server": "configs"}'
