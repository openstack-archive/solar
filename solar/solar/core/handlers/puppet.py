# -*- coding: utf-8 -*-
from contextlib import nested

from fabric import api as fabric_api
from fabric.contrib import project as fabric_project
import os

from solar.core.log import log
from solar.core.handlers.base import BaseHandler
from solar.core.provider import GitProvider


class ResourceSSHMixin(object):
    @staticmethod
    def _ssh_command(resource, *args, **kwargs):
        log.debug('SSH: %s', args)

        managers = [
            fabric_api.settings(**ResourceSSHMixin._fabric_settings(resource)),
        ]

        if 'cwd' in kwargs:
            managers.append(
                fabric_api.cd(kwargs['cwd'])
            )

        with nested(*managers):
            return fabric_api.run(' '.join(args))

    @staticmethod
    def _scp_command(resource, _from, _to):
        log.debug('SCP: %s -> %s', _from, _to)

        with fabric_api.settings(**ResourceSSHMixin._fabric_settings(resource)):
            return fabric_project.rsync_project(_to, local_dir=_from)

    @staticmethod
    def _fabric_settings(resource):
        return {
            'host_string': ResourceSSHMixin._ssh_command_host(resource),
            'key_filename': resource.args['ssh_key'].value,
        }

    @staticmethod
    def _ssh_command_host(resource):
        return '{}@{}'.format(resource.args['ssh_user'].value,
                              resource.args['ip'].value)


class LibrarianPuppet(ResourceSSHMixin):
    def __init__(self, resource, organization='openstack'):
        self.resource = resource
        self.organization = organization

    def install(self):
        puppet_module = '{}-{}'.format(
            self.organization,
            self.resource.metadata['puppet_module']
        )

        puppetlabs = self._ssh_command(
            self.resource,
            'sudo', 'cat', '/tmp/puppet-modules/Puppetfile'
        )

        git = self.resource.args['git'].value

        definition = "mod '{module_name}', :git => '{repository}', :ref => '{branch}'".format(
            module_name=puppet_module,
            repository=git['repository'],
            branch=git['branch']
        )

        modules = puppetlabs.split('\n')

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
            f.write('\n'.join(modules))

        self._scp_command(
            self.resource,
            '/tmp/Puppetfile',
            '/tmp/Puppetfile'
        )

        self._ssh_command(
            self.resource,
            'sudo', 'cp', '/tmp/Puppetfile', '/tmp/puppet-modules/Puppetfile'
        )

        self._ssh_command(
            self.resource,
            'sudo', 'librarian-puppet', 'install',
            cwd='/tmp/puppet-modules'
        )


# NOTE: We assume that:
# - puppet and hiera are installed
# - hiera-redis is installed with the 2.0 fix (https://github.com/GGenie/hiera-redis)
# - redis is installed and cluster set up with master (on slaves set up 'slaveof 10.0.0.2 6379')
# - redis keys are separated by colon (same as in hiera-redis backend)
class Puppet(ResourceSSHMixin, BaseHandler):
    def action(self, resource, action_name):
        log.debug('Executing Puppet manifest %s %s', action_name, resource)

        action_file = self._compile_action_file(resource, action_name)
        log.debug('action_file: %s', action_file)

        self.upload_manifests(resource)

        self._scp_command(resource, action_file, '/tmp/action.pp')

        self._ssh_command(
            resource, 'sudo', 'puppet', 'apply', '/tmp/action.pp'
        )

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
        modules = self._ssh_command(
            resource,
            'sudo', 'puppet', 'module', 'list'
        )

        module_installed = False
        for module in modules.decode('utf-8').split('\n'):
            if forge in module:
                module_installed = True
                break

        if not module_installed:
            self._ssh_command(
                resource,
                'sudo', 'puppet', 'module', 'install', forge
            )
        else:
            log.debug('Skipping module installation, already installed')

    def upload_manifests_librarian(self, resource):
        librarian = LibrarianPuppet(resource)
        librarian.install()

    def upload_manifests_git(self, resource):
        manifests_path = self.clone_manifests(resource)

        module_directory = '/etc/puppet/modules/{}'.format(
            resource.metadata['puppet_module']
        )
        self._ssh_command(
            resource,
            'sudo', 'rm', '-Rf', module_directory
        )
        self._ssh_command(
            resource, 'sudo', 'mkdir', '-p', module_directory
        )

        self._scp_command(resource, manifests_path, '/tmp')
        self._ssh_command(
            resource,
            'sudo', 'mv',
            '/tmp/{}/*'.format(os.path.split(manifests_path)[1]),
            module_directory
        )
