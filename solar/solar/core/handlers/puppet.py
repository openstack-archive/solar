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

import os

from solar.core.log import log
from solar.core.handlers.base import TempFileHandler
from solar.core.provider import GitProvider
from solar import errors


class LibrarianPuppet(object):
    def __init__(self, resource, organization='openstack', transport_sync=None, transport_run=None):
        self.resource = resource
        self.organization = organization
        self.transport_sync = transport_sync
        self.transport_run = transport_run

    def install(self):
        puppet_module = '{}-{}'.format(
            self.organization,
            self.resource.metadata['puppet_module']
        )

        puppetlabs = self.transport_run.run(
            self.resource,
            'sudo', 'cat', '/var/tmp/puppet/Puppetfile'
        )
        log.debug('Puppetlabs file is: \n%s\n', puppetlabs)

        git = self.resource.args['git'].value

        definition = "mod '{module_name}', :git => '{repository}', :ref => '{branch}'".format(
            module_name=puppet_module,
            repository=git['repository'],
            branch=git['branch']
        )

        modules = puppetlabs.split('\n')

        # remove forge entry
        modules = [module for module in modules if not module.startswith('forge')]

        idx = -1
        for i, module in enumerate(modules):
            if "mod '{}'".format(puppet_module) in module:
                log.debug('Module {} found in librarian Puppetfile, overwriting'.format(puppet_module))
                idx = i
                modules[i] = definition
                break

        if idx == -1:
            log.debug('Adding module {} to librarian Puppetfile'.format(puppet_module))
            modules.append(definition)

        with open('/tmp/Puppetfile', 'w') as f:
            f.write('\nforge "https://forge.puppetlabs.com"\n')
            f.write('\n'.join(modules))
            f.write('\n')

        self.transport_sync.copy(
            self.resource,
            '/tmp/Puppetfile',
            '/var/tmp/puppet/Puppetfile',
            use_sudo=True
        )

        self.transport_sync.sync_all()

        self.transport_run.run(
            self.resource,
            'sudo', 'librarian-puppet', 'install',
            cwd='/var/tmp/puppet'
        )


# NOTE: We assume that:
# - puppet and hiera are installed
# - hiera-redis is installed with the 2.0 fix (https://github.com/GGenie/hiera-redis)
# - redis is installed and cluster set up with master (on slaves set up 'slaveof 10.0.0.2 6379')
# - redis keys are separated by colon (same as in hiera-redis backend)
class Puppet(TempFileHandler):
    def action(self, resource, action_name):
        log.debug('Executing Puppet manifest %s %s', action_name, resource)

        action_file = self._compile_action_file(resource, action_name)
        log.debug('action_file: %s', action_file)

        self.upload_manifests(resource)

        self.prepare_templates_and_scripts(resource, action_file, '')
        self.transport_sync.copy(resource, action_file, '/tmp/action.pp')
        self.transport_sync.sync_all()

        cmd = self.transport_run.run(
            resource,
            'puppet', 'apply', '-vd', '/tmp/action.pp', '--detailed-exitcodes',
            env={
                'FACTER_resource_name': resource.name,
            },
            use_sudo=True,
            warn_only=True,
        )
        # 0 - no changes, 2 - successfull changes
        if cmd.return_code not in [0, 2]:
            raise errors.SolarError(
                'Puppet for {} failed with {}'.format(
                    resource.name, cmd.return_code))
        return cmd

    def clone_manifests(self, resource):
        git = resource.args['git'].value
        p = GitProvider(git['repository'], branch=git['branch'])

        return p.directory

    def upload_manifests(self, resource):
        if 'forge' in resource.args and resource.args['forge'].value:
            self.upload_manifests_forge(resource)
        else:
            self.upload_manifests_librarian(resource)

    def upload_manifests_forge(self, resource):
        forge = resource.args['forge'].value

        # Check if module already installed
        modules = self.transport_run.run(
            resource,
            'sudo', 'puppet', 'module', 'list'
        )

        module_installed = False
        for module in modules.decode('utf-8').split('\n'):
            if forge in module:
                module_installed = True
                break

        if not module_installed:
            self.transport_run.run(
                resource,
                'sudo', 'puppet', 'module', 'install', forge
            )
        else:
            log.debug('Skipping module installation, already installed')

    def upload_manifests_librarian(self, resource):
        librarian = LibrarianPuppet(resource,
                                    transport_run=self.transport_run,
                                    transport_sync=self.transport_sync)
        librarian.install()

    def upload_manifests_git(self, resource):
        manifests_path = self.clone_manifests(resource)

        module_directory = '/etc/puppet/modules/{}'.format(
            resource.metadata['puppet_module']
        )
        self.transport_run.run(
            resource,
            'sudo', 'rm', '-Rf', module_directory
        )
        self.transport_run.run(
            resource, 'sudo', 'mkdir', '-p', module_directory
        )

        self.transport_sync.copy(resource, manifests_path, '/tmp')
        self.transport_sync.sync_all()

        self.transport_run.run(
            resource,
            'sudo', 'mv',
            '/tmp/{}/*'.format(os.path.split(manifests_path)[1]),
            module_directory
        )
