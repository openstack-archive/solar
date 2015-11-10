#!/usr/bin/env python

import os
import sys
import yaml
import json

CURDIR = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(CURDIR, 'test_sample.yaml')) as f:
    ARGS = yaml.safe_load(f)

sys.stdout.write(json.dumps(ARGS))
