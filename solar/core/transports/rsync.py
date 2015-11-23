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

from fabric import api as fabric_api

from solar.core.log import log
from solar.core.transports.base import SyncTransport, Executor

# XXX:
# currently we don't support key verification or acceptation
# so if you want to play with RsyncTransport you need to verify the keys before
# just ssh from root on traget nodes


class RsyncSyncTransport(SyncTransport):

    def _rsync_props(self, resource):
        transport = self.get_transport_data(resource)
        host = resource.ip()
        user = transport['user']
        port = transport['port']
        # TODO: user port somehow
        key = transport['key']
        return {
            'ssh_key': key,
            'ssh_user': user,
            'host_string': '{}@{}'.format(user, host)
        }

    def copy(self, resource, _from, _to, use_sudo=False):
        log.debug("RSYNC: %s -> %s", _from, _to)
        if use_sudo:
            rsync_path = "sudo rsync"
        else:
            rsync_path = "rsync"
        rsync_props = self._rsync_props(resource)
        rsync_cmd = ('rsync -az -e "ssh -i %(ssh_key)s" '
                     '--rsync-path="%(rsync_path)s" %(_from)s '
                     '%(rsync_host)s:%(_to)s') % dict(
                         rsync_path=rsync_path,
                         ssh_key=rsync_props['ssh_key'],
                         rsync_host=rsync_props['host_string'],
                         _from=_from,
                         _to=_to)

        rsync_executor = lambda transport: fabric_api.local(
            rsync_cmd
        )

        log.debug("RSYNC CMD: %r" % rsync_cmd)

        executor = Executor(resource=resource,
                            executor=rsync_executor,
                            params=(_from, _to, use_sudo))
        self.executors.append(executor)
