#!/bin/bash
set -xe

export ENV_NAME="solar-example"
export SLAVES_COUNT=2
export DEPLOY_TIMEOUT=2400
export TEST_SCRIPT="/vagrant/examples/openstack/openstack.py create_all"

./utils/jenkins/run.sh 
