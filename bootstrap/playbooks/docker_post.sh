#!/bin/sh
# FIXME(bogdando) additional teardown steps after docker
# asks for sudo password
docker network rm solar
docker stop vagrant_pg_1
docker stop  vagrant_riak_1
docker rm vagrant_pg_1
docker rm  vagrant_riak_1
sudo rm -rf /tmp/solar*
sudo rm -rf tmp
sudo rm -f .vagrant/machines/solar-dev*/virtualbox/private_key
