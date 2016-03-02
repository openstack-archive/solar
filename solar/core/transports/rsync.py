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
from solar.core.transports.base import Executor
from solar.core.transports.base import SyncTransport
from solar.utils import execute

# XXX:
# currently we don't support key verification or acceptation
# so if you want to play with RsyncTransport you need to verify the keys before
# just ssh from root on traget nodes


class RsyncSyncTransport(SyncTransport):

    _priority = 10

    def _rsync_props(self, resource):
        transport = self.get_transport_data(resource)
        host = resource.ip()
        user = transport['user']
        # port = transport['port']
        # TODO: user port somehow
        key = transport.get('key')
        password = transport.get('password')
        return {
            'ssh_key': key,
            'ssh_password': password,
            'ssh_user': user,
            'host_string': '{}@{}'.format(user, host)
        }

    def _ssh_cmd(self, settings):
        if settings['ssh_key']:
            return ('ssh', '-i', settings['ssh_key'])
        elif settings['ssh_password']:
            return ('sshpass', '-e', 'ssh')
        else:
            raise Exception("No key and no password given")

    def copy(self, resource, _from, _to, use_sudo=False):
        log.debug("RSYNC: %s -> %s", _from, _to)
        if os.path.isdir(_from):
            r_dir_path = _to
        else:
            r_dir_path = _to.rsplit('/', 1)[0]
        if use_sudo:
            rsync_path = "sudo mkdir -p {} && sudo rsync".format(r_dir_path)
        else:
            rsync_path = "mkdir -p {} && rsync".format(r_dir_path)

        rsync_props = self._rsync_props(resource)
        ssh_cmd = ' '.join(self._ssh_cmd(rsync_props))
        rsync_cmd = ('rsync -az -e "%(ssh_cmd)s" '
                     '--rsync-path="%(rsync_path)s" %(_from)s '
                     '%(rsync_host)s:%(_to)s') % dict(
                         rsync_path=rsync_path,
                         ssh_cmd=ssh_cmd,
                         rsync_host=rsync_props['host_string'],
                         _from=_from,
                         _to=_to)

        if rsync_props.get('ssh_password'):
            env = os.environ.copy()
            env['SSHPASS'] = rsync_props['ssh_password']
        else:
            env = os.environ

        rsync_executor = lambda transport: execute(
            rsync_cmd, shell=True, env=env)

        log.debug("RSYNC CMD: %r" % rsync_cmd)

        executor = Executor(resource=resource,
                            executor=rsync_executor,
                            params=(_from, _to, use_sudo))
        self.executors.append(executor)
