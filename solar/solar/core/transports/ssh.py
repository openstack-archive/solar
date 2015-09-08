import os
from functools import partial
from contextlib import nested

from fabric import api as fabric_api
from fabric.contrib import project as fabric_project

from solar.core.log import log
from solar.core.transports.base import RunTransport, SyncTransport, Executor


class _SSHTransport(object):

    # TODO: maybe static/class method ?
    def _fabric_settings(self, resource):
        return {
            'host_string': self._ssh_command_host(resource),
            'key_filename': resource.args['ssh_key'].value,
        }

    # TODO: maybe static/class method ?
    def _ssh_command_host(self, resource):
        return '{}@{}'.format(resource.args['ssh_user'].value,
                              resource.args['ip'].value)


class SSHSyncTransport(SyncTransport, _SSHTransport):

    def __init__(self):
        SyncTransport.__init__(self)

    def _copy_file(self, resource, _from, _to, use_sudo=False):
        executor = lambda transport: fabric_project.put(
            remote_path=_to,
            local_path=_from,
            use_sudo=use_sudo
        )
        return executor

    def _copy_directory(self, resource, _from, _to, use_sudo=False):
        executor = lambda transport: fabric_project.upload_project(
            remote_dir=_to,
            local_dir=_from,
            use_sudo=use_sudo
        )
        return executor

    def copy(self, resource, _from, _to, use_sudo=False):
        log.debug('SCP: %s -> %s', _from, _to)

        if os.path.isfile(_from):
            executor = self._copy_file(resource, _from, _to, use_sudo)
        else:
            executor = self._copy_directory(resource, _from, _to, use_sudo)

        # with fabric_api.settings(**self._fabric_settings(resource)):
        #     return executor()
        executor = Executor(resource=resource,
                            executor=executor,
                            params=(_from, _to, use_sudo))
        self.executors.append(executor)

    def run_all(self):
        for executor in self.executors:
            resource = executor.resource
            with fabric_api.settings(**self._fabric_settings(resource)):
                executor.run(self)


class SSHRunTransport(RunTransport, _SSHTransport):

    def run(self, resource, *args, **kwargs):
        log.debug('SSH: %s', args)

        executor = fabric_api.run
        if kwargs.get('use_sudo', False):
            executor = fabric_api.sudo

        managers = [
            fabric_api.settings(**self._fabric_settings(resource)),
        ]

        cwd = kwargs.get('cwd')
        if cwd:
            managers.append(fabric_api.cd(kwargs['cwd']))

        env = kwargs.get('env')
        if env:
            managers.append(fabric_api.shell_env(**kwargs['env']))

        if kwargs.get('warn_only', False):
            managers.append(fabric_api.warn_only())

        with nested(*managers):
            return executor(' '.join(args))
