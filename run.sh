#!/bin/bash

# required for ease of development
if [ -d /solar ]; then
  cd /solar && python setup.py develop
fi

#used only to start celery on docker
ansible-playbook -v -i "localhost," -c local /celery.yaml --skip-tags slave

tail -f /var/run/celery/*.log
