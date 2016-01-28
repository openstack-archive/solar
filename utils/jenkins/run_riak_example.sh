#!/bin/bash
set -xe

export SLAVES_COUNT=3
export DEPLOY_TIMEOUT=600
export TEST_SCRIPT="/usr/bin/python /vagrant/solar-resources/examples/riak/riaks.py create_all"

./utils/jenkins/run.sh
