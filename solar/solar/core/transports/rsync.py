from fabric import api as fabric_api

from solar.core.log import log
from solar.core.transports.base import SyncTransport, Executor

# XXX:
# currently we don't support key verification or acceptation
# so if you want to play with RsyncTransport you need to verify the keys before
# just ssh from root on traget nodes


class RsyncSyncTransport(SyncTransport):

    def _rsync_props(self, resource):
        return {
            'ssh_key': resource.args['ssh_key'].value,
            'ssh_user': resource.args['ssh_user'].value
        }

    def _rsync_command_host(self, resource):
        return '{}@{}'.format(resource.args['ssh_user'].value,
                              resource.args['ip'].value)

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
                         rsync_host=self._rsync_command_host(resource),
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
