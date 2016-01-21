#!/bin/bash
set -xe

export SLAVES_COUNT=1
export DEPLOY_TIMEOUT=300
export TEST_SCRIPT="/bin/bash /vagrant/solar-resources/examples/wordpress/run.sh"

./utils/jenkins/run.sh
