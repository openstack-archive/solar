# -*- coding: utf-8 -*-
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

import yaml

from solar.core.handlers.base import TempFileHandler
from solar.core.log import log
from solar import errors


# NOTE: We assume that:
# - puppet is installed
class Puppet(TempFileHandler):

    def action(self, resource, action_name):
        log.debug('Executing Puppet manifest %s %s',
                  action_name, resource.name)

        action_file = self._compile_action_file(resource, action_name)
        log.debug('action_file: %s', action_file)

        self.upload_hiera_resource(resource)

        action_file_name = '/tmp/{}.pp'.format(resource.name)

        self.prepare_templates_and_scripts(resource, action_file, '')
        self.transport_sync.copy(resource, action_file, action_file_name)
        self.transport_sync.sync_all()

        cmd_args = ['puppet', 'apply', '-vd',
                    action_file_name,
                    '--detailed-exitcodes']
        if 'puppet_modules' in resource.args:
            cmd_args.append('--modulepath={}'.format(
                resource.args['puppet_modules']))

        cmd = self.transport_run.run(
            resource,
            *cmd_args,
            env={
                'FACTER_resource_name': resource.name,
            },
            use_sudo=True,
            warn_only=True
        )
        # 0 - no changes, 2 - successfull changes
        if cmd.return_code not in [0, 2]:
            raise errors.SolarError(
                'Puppet for {} failed with {}'.format(
                    resource.name, cmd.return_code))
        return cmd

    def _make_args(self, resource):
        return {resource.name: {'input': resource.args}}

    def upload_hiera_resource(self, resource):
        src = '/tmp/puppet_{}.yaml'.format(resource.name)
        with open(src, 'w') as f:
            f.write(yaml.safe_dump(self._make_args(resource)))

        self.transport_sync.copy(
            resource,
            src,
            '/etc/puppet/hieradata/{}.yaml'.format(resource.name),
            use_sudo=True
        )
        self.transport_sync.sync_all()


class PuppetV2(Puppet):

    def _make_args(self, resource):
        return resource.args
