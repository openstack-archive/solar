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
"""Solar CLI api

On create "golden" resource should be moved to special place
"""

import subprocess

from copy import deepcopy

import sys

import textwrap
import argparse
import yaml

from solar import utils
from solar.core import ansible
from solar.interfaces.db import Storage
from solar.interfaces.db.dir import DirDBM


class Cmd(object):

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description=textwrap.dedent(__doc__),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        self.subparser = self.parser.add_subparsers(
            title='actions',
            description='Supported actions',
            help='Provide of one valid actions')
        self.register_actions()
        self.dbm = DirDBM('tmp/created/')

    def register_actions(self):
        parser = self.subparser.add_parser('create')
        parser.set_defaults(func=getattr(self, 'create'))
        parser.add_argument(
            '-r',
            '--resource',
            required=True)
        parser.add_argument(
            '-t', '--tags', nargs='+',
            help='Identifier or resource'
            )

        parser = self.subparser.add_parser('prepare')
        parser.set_defaults(func=getattr(self, 'prepare'))
        parser.add_argument(
            '-a',
            '--action',
            required=True)
        parser.add_argument(
            '-r',
            '--resources',
            nargs='+',
            required=True)

        parser = self.subparser.add_parser('exec')
        parser.set_defaults(func=getattr(self, 'execute'))
        parser.add_argument(
            '-a',
            '--action',
            required=True)
        parser.add_argument(
            '-r',
            '--resources',
            nargs='+',
            required=True)

        parser = self.subparser.add_parser('show')
        parser.set_defaults(func=getattr(self, 'show'))
        parser.add_argument(
            '-r',
            '--resource',
            required=True)

        parser = self.subparser.add_parser('clear')
        parser.set_defaults(func=getattr(self, 'clear'))

    def parse(self, args):
        parsed = self.parser.parse_args(args)
        return parsed.func(parsed)

    def create(self, args):
        resource = args.resource

        storage = Storage.from_files('./schema/resources')

        resource_uid = '{0}_{1}'.format(resource, '_'.join(args.tags))
        data = deepcopy(storage.get(resource))
        data['tags'] = args.tags
        self.dbm[resource_uid] = yaml.dump(
            data, default_flow_style=False)

    def clear(self, args):
        self.dbm.clear()

    def show(self, args):
        print self.dbm[args.resource]

    def prepare(self, args):

        orch = ansible.AnsibleOrchestration(
            [yaml.load(self.dbm[r]) for r in args.resources])

        utils.create_dir('tmp/group_vars')
        with open('tmp/hosts', 'w') as f:
            f.write(orch.inventory)

        with open('tmp/group_vars/all', 'w') as f:
            f.write(yaml.dump(orch.vars, default_flow_style=False))

        with open('tmp/main.yml', 'w') as f:
            f.write(
                yaml.dump(getattr(orch, args.action)(),
                default_flow_style=False))

    def execute(self, args):
        self.prepare(args)
        sub = subprocess.Popen(
            ['ansible-playbook', '-i', 'tmp/hosts', 'tmp/main.yml'])
        out, err = sub.communicate()
        print out

def main():
    api = Cmd()
    api.parse(sys.argv[1:])
