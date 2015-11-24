#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License attached#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See then
#    License for the specific language governing permissions and limitations
#    under the License.

from fabric import api as fabric_api
from solar.core.log import log
from solar.core.transports.base import RunTransport


class _RawSSHTransport(object):

    def _ssh_props(self, resource):
        return {
            'ssh_key': resource.args['ssh_key'].value,
            'ssh_user': resource.args['ssh_user'].value
        }

    def _ssh_command_host(self, resource):
        return '{}@{}'.format(resource.args['ssh_user'].value,
                              resource.args['ip'].value)

    def _ssh_cmd(self, resource):
        props = self._ssh_props(resource)
        return ('ssh', '-i', props['ssh_key'])



class RawSSHRunTransport(RunTransport, _RawSSHTransport):

    def run(self, resource, *args, **kwargs):
        log.debug("RAW SSH: %s", args)

        cmds = []
        cwd = kwargs.get('cwd')
        if cwd:
            cmds.append(('cd', cwd))

        cmds.append(args)

        if kwargs.get('use_sudo', False):
            cmds = [('sudo', ) + cmd for cmd in cmds]

        cmds = [' '.join(cmd) for cmd in cmds]

        remote_cmd = '\"%s\"' % ' && '.join(cmds)

        ssh_cmd = self._ssh_cmd(resource)
        ssh_cmd += (self._ssh_command_host(resource), remote_cmd)

        log.debug("SSH CMD: %r", ssh_cmd)

        return fabric_api.local(' '.join(ssh_cmd))

