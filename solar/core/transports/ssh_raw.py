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
from solar.core.transports.base import RunTransport
from solar.utils import execute


class _RawSSHTransport(object):

    def settings(self, resource):
        transport = self.get_transport_data(resource)
        host = resource.ip()
        user = transport['user']
        port = transport['port']
        key = transport.get('key')
        password = transport.get('password')
        return {'ssh_user': user,
                'ssh_key': key,
                'ssh_password': password,
                'port': port,
                'ip': host}

    def _ssh_command_host(self, settings):
        return '{}@{}'.format(settings['ssh_user'],
                              settings['ip'])

    def _ssh_cmd(self, settings):
        if settings['ssh_key']:
            return ('ssh', '-i', settings['ssh_key'])
        elif settings['ssh_password']:
            return ('sshpass', '-e', 'ssh')
        else:
            raise Exception("No key and no password given")


class RawSSHRunTransport(RunTransport, _RawSSHTransport):

    def run(self, resource, *args, **kwargs):
        log.debug("RAW SSH: %s", args)

        commands = []
        prefix = []
        if kwargs.get('use_sudo', False):
            prefix.append('sudo')

        if kwargs.get('cwd'):
            cmd = prefix + ['cd', kwargs['cwd']]
            commands.append(' '.join(cmd))

        env = []
        if 'env' in kwargs:
            for key, value in kwargs['env'].items():
                env.append('{}={}'.format(key, value))

        cmd = prefix + env + list(args)
        commands.append(' '.join(cmd))

        remote_cmd = '\"%s\"' % ' && '.join(commands)

        settings = self.settings(resource)
        if settings.get('ssh_password'):
            env = os.environ.copy()
            env['SSHPASS'] = settings['ssh_password']
        else:
            env = os.environ
        ssh_cmd = self._ssh_cmd(settings)
        ssh_cmd += (self._ssh_command_host(settings), remote_cmd)

        log.debug("RAW SSH CMD: %r", ssh_cmd)
        # TODO convert it to SolarRunResult

        return execute(' '.join(ssh_cmd), shell=True, env=env)
