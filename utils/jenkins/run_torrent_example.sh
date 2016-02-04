#!/bin/bash
set -xe

export SLAVES_COUNT=2
export DEPLOY_TIMEOUT=240
export TEST_SCRIPT="/usr/bin/python /vagrant/solar-resources/examples/torrent/example.py"

./utils/jenkins/run.sh
