#!/bin/bash
set -xe

export ENV_NAME="solar-example"
export SLAVES_COUNT=1
export DEPLOY_TIMEOUT=300
export TEST_SCRIPT="/bin/bash /vagrant/solar-resources/examples/wordpress/run.sh"

./utils/jenkins/run.sh

