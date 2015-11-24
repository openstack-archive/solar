#!/bin/bash

# required for ease of development
python setup.py develop

pushd /solard
python setup.py develop
popd

#used only to start celery on docker
ansible-playbook -v -i "localhost," -c local /celery.yaml --skip-tags slave

tail -f /var/run/celery/*.log
