#!/bin/bash

# required for ease of development
pushd /solar
python setup.py develop
popd

pushd /solard
python setup.py develop
popd

tail -f /var/run/celery/*.log
