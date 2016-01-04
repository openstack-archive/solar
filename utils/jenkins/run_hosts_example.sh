#!/bin/bash
set -xe

export ENV_NAME="solar-example"
export SLAVES_COUNT=2
export DEPLOY_TIMEOUT=180
export TEST_SCRIPT="/vagrant/examples/hosts_file/hosts.py"

./utils/jenkins/run.sh 
