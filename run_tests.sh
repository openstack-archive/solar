#!/bin/bash

set -e


VENV=x-venv
WORKSPACE=${WORKSPACE:-"/vagrant"}
CONFIG_FILE=$WORKSPACE/jenkins-config.yaml

# Setup a proper path, I call my virtualenv dir "$VENV" and
# I've got the virtualenv command installed in /usr/local/bin
PATH=$WORKSPACE/venv/bin:/usr/local/bin:$PATH
if [ ! -d "$VENV" ]; then
    virtualenv -p python2 $VENV
fi

. $VENV/bin/activate

pip install -r solar/test-requirements.txt --download-cache=/tmp/$JOB_NAME

pushd solar/solar

PYTHONPATH=$WORKSPACE/solar CONFIG_FILE=$CONFIG_FILE py.test -s test/

popd
