#!/usr/bin/env python

import os
import sys
from subprocess import Popen, PIPE
import yaml
import json

CURDIR = os.path.dirname(os.path.realpath(__file__))

ARGS = json.loads(sys.stdin.read())

def execute(command, **env_vars):
    env = os.environ.copy()
    for var in env_vars:
        env[var] = env_vars[var]
    popen = Popen(command, stdin=PIPE, stdout=PIPE, env=env)
    return popen.communicate()

def prepare_hiera():
    hiera_conf = """:backends:
  - yaml
:yaml:
  :datadir: /etc/puppet/hieradata
:hierarchy:
  - {}
""".format(ARGS['uid'])
    with open('/etc/puppet/' + ARGS['uid'] + 'globals.yaml', 'w') as f:
        f.write('')

    with open('/etc/puppet/hiera.yaml', 'w') as f:
        f.write(hiera_conf)

    with open('/etc/puppet/hieradata/{}.yaml'.format(ARGS['uid']), 'w') as f:
        f.write(yaml.safe_dump(ARGS))

def run_command():
    cmd = [
        'puppet', 'apply', '--modulepath={}'.format(ARGS['puppet_modules']),
        os.path.join(CURDIR, 'globals.pp')]
    return execute(cmd)

def collect_results():
    path = '/etc/puppet/' + ARGS['uid'] + 'globals.yaml'
    with open(path) as f:
        return yaml.safe_load(f)

def main():
    prepare_hiera()
    run_command()
    rst = collect_results()
    sys.stdout.write(json.dumps(rst))

if __name__ == '__main__':
    main()
