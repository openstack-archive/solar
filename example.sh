#!/bin/bash
set -eux

rm /vagrant/tmp/storage/* || true
rm /vagrant/tmp/connections.yaml || true
find /vagrant/solar/solar -name '*.pyc' -delete || true

sudo docker stop $(sudo docker ps -q) || true

solar profile -c -t env/test_env -i prf1
solar discover

solar assign -n 'node/node_2 | node/node_1' -r 'resources/docker'
solar assign -n 'node/node_1' -r 'resources/mariadb'
solar assign -n 'node/node_1' -r 'resources/keystone'
solar assign -n 'node/node_1' -r 'resources/haproxy'

solar connect --profile prf1

solar run -a run -t 'resources/docker'

solar run -a run -t 'resource/mariadb_service'
solar run -a run -t 'resource/mariadb_keystone_db'
solar run -a run -t 'resource/mariadb_keystone_user'

solar run -a run -t 'resource/keystone_config'
solar run -a run -t 'resource/keystone_service'

solar run -a run -t 'resource/haproxy_config'
solar run -a run -t 'resources/haproxy'
