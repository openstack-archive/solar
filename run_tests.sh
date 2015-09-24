#!/bin/bash
#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

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

PYTHONPATH=$WORKSPACE/solar CONFIG_FILE=$CONFIG_FILE py.test --cov=solar -s test/

popd
