#!/bin/bash
set -xe

export ENV_NAME="${ENV_NAME}"

export SLAVES_COUNT=2
export DEPLOY_TIMEOUT=2400
export TEST_SCRIPT="/usr/bin/python /vagrant/solar-resources/examples/openstack/openstack.py create_all"

./utils/jenkins/run.sh
