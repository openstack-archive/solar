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
from contextlib import nested

from fabric import api as fabric_api
from fabric.contrib import project as fabric_project

from solar.core.log import log
from solar.core.transports.base import RunTransport, SyncTransport, Executor


class _SSHTransport(object):

    def _fabric_settings(self, resource):
        transport = self.get_transport_data(resource)
        host = resource.ip()
        user = transport['user']
        port = transport['port']
        key = transport['key']
        return {
            'host_string': "{}@{}:{}".format(user, host, port),
            'key_filename': key,
        }


class SSHSyncTransport(SyncTransport, _SSHTransport):

    preffered_transport_name = 'ssh'

    def __init__(self):
        _SSHTransport.__init__(self)
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

    preffered_transport_name = 'ssh'

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
