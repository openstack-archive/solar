#!/bin/bash

# required for ease of development
if [ -d /solar ]; then
  cd /solar && python setup.py develop
fi

celery worker -A solar.orchestration.runner -P gevent -c 1000 -Q system_log,celery,scheduler
