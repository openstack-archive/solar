#!/bin/sh
# FIXME(bogdando) w/a unimplemented docker networking, see
# https://github.com/mitchellh/vagrant/issues/6667.
# Create the docker solar net
if ! docker network inspect solar >/dev/null 2>&1 ; then
  docker network create -d bridge \
    -o "com.docker.network.bridge.enable_icc"="true" \
    -o "com.docker.network.bridge.enable_ip_masquerade"="true" \
    -o "com.docker.network.driver.mtu"="1500" \
    --gateway=$1 --ip-range=$2 --subnet=$3 \
    solar >/dev/null 2>&1
fi
