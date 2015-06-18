# -*- coding: utf-8 -*-
import os
import subprocess

from solar.core.log import log
from solar.core.handlers.base import BaseHandler


class Puppet(BaseHandler):
    def action(self, resource, action_name):
        # inventory_file = self._create_inventory(resource)
        # playbook_file = self._create_playbook(resource, action_name)
        # log.debug('inventory_file: %s', inventory_file)
        # log.debug('playbook_file: %s', playbook_file)
        # call_args = ['ansible-playbook', '--module-path', '/vagrant/library', '-i', inventory_file, playbook_file]
        # log.debug('EXECUTING: %s', ' '.join(call_args))
        #
        # try:
        #     subprocess.check_output(call_args)
        # except subprocess.CalledProcessError as e:
        #     log.error(e.output)
        #     log.exception(e)
        #     raise

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
            '{}:/tmp/'.format(self._ssh_command_host(resource))
        )

        self._ssh_command(
            resource, 'sudo', 'mv', '/tmp/puppet/*', module_directory
        )

        self._scp_command(
            resource,
            action_file,
            '{}:/tmp/action.pp'.format(self._ssh_command_host(resource))
        )

        self._ssh_command(
            resource, 'sudo', 'puppet', 'apply', '/tmp/action.pp'
        )

    def _ssh_command(self, resource, *args):
        print 'SSH ', args

        return subprocess.check_output([
            'ssh',
            self._ssh_command_host(resource),
            '-i', resource.args['ssh_key'].value,
            ] + list(args)
        )

    def _scp_command(self, resource, _from, _to):
        print 'SCP: ', _from, _to

        try:
            return subprocess.check_output([
                'scp', '-r', '-i', resource.args['ssh_key'].value, _from, _to
            ])
        except Exception as e:
            import pudb; pudb.set_trace()

    def _ssh_command_host(self, resource):
        return '{}@{}'.format(resource.args['ssh_user'].value,
                              resource.args['ip'].value)
