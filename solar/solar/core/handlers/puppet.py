# -*- coding: utf-8 -*-
from fabric import api as fabric_api
from fabric.contrib import project as fabric_project
import os

from solar.core.log import log
from solar.core.handlers.base import BaseHandler


# NOTE: We assume that:
# - puppet and hiera are installed
# - hiera-redis is installed with the 2.0 fix (https://github.com/GGenie/hiera-redis)
# - redis is installed and cluster set up with master (on slaves set up 'slaveof 10.0.0.2 6379')
# - redis keys are separated by colon (same as in hiera-redis backend)
class Puppet(BaseHandler):
    def action(self, resource, action_name):
        print 'Executing Puppet manifest ', action_name, resource

        action_file = self._compile_action_file(resource, action_name)
        log.debug('action_file: %s', action_file)

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

        self._scp_command(
            resource,
            os.path.join(resource.metadata['base_path'], 'puppet'),
            '/tmp'
        )
        self._ssh_command(
            resource, 'sudo', 'mv', '/tmp/puppet/*', module_directory
        )

        self._scp_command(resource, action_file, '/tmp/action.pp')

        self._ssh_command(
            resource, 'sudo', 'puppet', 'apply', '/tmp/action.pp'
        )

    def _ssh_command(self, resource, *args):
        print 'SSH ', args

        with fabric_api.settings(**self._fabric_settings(resource)):
            return fabric_api.run(' '.join(args))

    def _scp_command(self, resource, _from, _to):
        print 'SCP: ', _from, _to

        with fabric_api.settings(**self._fabric_settings(resource)):
            #return fabric_api.put(_from, _to)
            return fabric_project.rsync_project(_to, local_dir=_from)


    def _fabric_settings(self, resource):
        return {
            'host_string': self._ssh_command_host(resource),
            'key_filename': resource.args['ssh_key'].value,
        }

    def _ssh_command_host(self, resource):
        return '{}@{}'.format(resource.args['ssh_user'].value,
                              resource.args['ip'].value)
