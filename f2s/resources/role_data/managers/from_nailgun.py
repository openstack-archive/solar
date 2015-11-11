#!/usr/bin/env python

import sys
import json

from fuelclient.objects.environment import Environment

ARGS = json.loads(sys.stdin.read())

env = Environment(ARGS['env'])
facts = env.get_default_facts('deployment', [ARGS['uid']])

sys.stdout.write(json.dumps(facts[0]))
