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

import sys

import textwrap
import argparse
import yaml

from solar import utils
from solar import extensions
from solar.interfaces.db import get_db

# NOTE: these are extensions, they shouldn't be imported here
from solar.extensions.modules import ansible
from solar.extensions.modules.discovery import Discovery


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
        self.db = get_db()

    def register_actions(self):
        parser = self.subparser.add_parser('create')
        parser.set_defaults(func=getattr(self, 'create'))
        parser.add_argument(
            '-r',
            '--resource',
            required=True)
        parser.add_argument(
            '-t', '--tags', nargs='+',
            help='Identifier or resource')

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

        parser = self.subparser.add_parser('discover')
        parser.set_defaults(func=getattr(self, 'discover'))

        parser = self.subparser.add_parser('clear')
        parser.set_defaults(func=getattr(self, 'clear'))

        # Perform configuration
        parser = self.subparser.add_parser('configure')
        parser.set_defaults(func=getattr(self, 'configure'))
        parser.add_argument(
            '-p',
            '--profile')

    def configure(self, args):
        extensions.find_by_provider_from_profile(args.profile, 'configure').configure()

    def discover(self, args):
        Discovery({'id': 'discovery'}).execute()

    def parse(self, args):
        parsed = self.parser.parse_args(args)
        return parsed.func(parsed)

    def create(self, args):
        self.db.create_resource(args.resource, args.tags)

    def clear(self, args):
        self.db.clear()

    def show(self, args):
        print self.db[args.resource]

    def prepare(self, args):

        orch = ansible.AnsibleOrchestration(
            [yaml.load(self.db[r]) for r in args.resources])

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
