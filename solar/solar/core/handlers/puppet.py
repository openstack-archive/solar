# -*- coding: utf-8 -*-
import os
import subprocess
import yaml

from solar.core.log import log
from solar.core.handlers.base import BaseHandler


class Puppet(BaseHandler):
    def action(self, resource, action_name):
        print 'Executing Puppet manifest ', action_name, resource

        action_file = self._compile_action_file(resource, action_name)
        log.debug('action_file: %s', action_file)

        hieradata_directory = '/etc/puppet/hieradata'
        self._ssh_command(
            resource, 'sudo', 'mkdir', '-p', hieradata_directory
        )
        hiera_file = '/tmp/hiera.yaml'
        # TODO: fix hierarchy
        with open(hiera_file, 'w') as f:
            f.write("""
:backends:
  - yaml
  - json
:yaml:
  :datadir: /etc/puppet/hieradata
:json:
  :datadir: /etc/puppet/hieradata
:hierarchy:
  - {}
            """.format(resource.name))
        self._scp_command(
            resource,
            hiera_file,
            '{}:/tmp/'.format(self._ssh_command_host(resource))
        )
        self._ssh_command(
            resource, 'sudo', 'mv', hiera_file, '/etc/puppet'
        )

        hiera_config_file = '/tmp/{}.yaml'.format(resource.name)
        with open(hiera_config_file, 'w') as f:
            f.write(yaml.dump(self._args_dict_for_hiera(resource),
                              default_flow_style=False))
        self._scp_command(
            resource,
            hiera_config_file,
            '{}:/tmp/'.format(self._ssh_command_host(resource))
        )
        self._ssh_command(
            resource, 'sudo', 'mv', hiera_config_file, hieradata_directory
        )

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

    def _args_dict_for_hiera(self, resource):
        ret = {}
        for k, v in resource.args_dict().items():
            ret['{}::{}'.format(resource.name, k)] = v

        return ret

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
