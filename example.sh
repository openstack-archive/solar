#!/bin/bash
set -eux

rm -rf /tmp/tmp*
rm /tmp/storage/* || true
rm /tmp/connections.yaml || true

mkdir -p /tmp/state

echo > /tmp/state/commit_log || true
echo > /tmp/state/commited_data || true
echo > /tmp/state/stage_log || true
find /vagrant/solar/solar -name '*.pyc' -delete || true

sudo docker stop $(sudo docker ps -q) || true
sudo docker rm $(sudo docker ps -qa) || true

solar profile -c -t env/test_env -i prf1
solar discover

solar assign -n 'node/node_2 | node/node_1' -r 'resources/docker'
solar assign -n 'node/node_1' -r 'resources/mariadb'
solar assign -n 'node/node_1' -r 'resources/keystone'
solar assign -n 'node/node_1' -r 'resources/haproxy'
solar assign -n 'node/node_1' -r 'resources/rabbitmq'

solar connect --profile prf1

./cli.py changes stage
./cli.py changes commit
