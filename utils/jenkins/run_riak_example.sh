#!/bin/bash
set -xe

export ENV_NAME="solar-example"
export SLAVES_COUNT=3
export DEPLOY_TIMEOUT=300
export TEST_SCRIPT="/usr/bin/python /vagrant/solar-resources/examples/riak/riaks.py create_all"

./utils/jenkins/run.sh
