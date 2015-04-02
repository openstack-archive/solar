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


import sys

import argparse
import yaml

from solar.core import ansible
from solar.interfaces.db import Storage


def parse():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-a',
        '--action',
        help='action to execute',
        required=True)

    parser.add_argument(
        '-r',
        '--resources',
        help='list of resources',
        nargs='+',
        required=True)

    return parser.parse_args()


def main():
    args = parse()

    print 'ACTION %s' % args.action
    print 'RESOURCES %s' % args.resources

    storage = Storage.from_files('./schema/resources')
    orch = ansible.AnsibleOrchestration(
        [storage.get(r) for r in args.resources])


    with open('tmp/hosts', 'w') as f:
        f.write(orch.inventory)

    with open('tmp/group_vars/all', 'w') as f:
        f.write(yaml.dump(orch.vars, default_flow_style=False))

    with open('tmp/main.yml', 'w') as f:
        f.write(
            yaml.dump(getattr(orch, args.action)(),
            default_flow_style=False))
