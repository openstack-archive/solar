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

from contextlib import nested
import os

from fabric import api as fabric_api
from fabric.contrib import project as fabric_project

from solar.core.log import log
from solar.core.transports.base import Executor
from solar.core.transports.base import RunTransport
from solar.core.transports.base import SolarTransportResult
from solar.core.transports.base import SyncTransport
from solar import errors


class ExecutorForFabric(Executor):

    def _abort_exception(self, output):
        raise errors.SolarError(output)


class _SSHTransport(object):

    _priority = 1

    def settings(self, resource):
        transport = self.get_transport_data(resource)
        host = resource.ip()
        user = transport['user']
        port = transport['port']
        settings = {
            'host_string': "{}@{}:{}".format(user, host, port),
        }
        settings['port'] = port
        settings['host'] = host
        key = transport.get('key', None)
        password = transport.get('password', None)
        if not key and not password:
            raise Exception("No key and no password given")
        elif not key:
            settings['password'] = password
        elif not password:
            settings['key_filename'] = key
        return settings


class SSHSyncTransport(SyncTransport, _SSHTransport):

    preffered_transport_name = 'ssh'

    def __init__(self):
        _SSHTransport.__init__(self)
        SyncTransport.__init__(self)

    def _ensure_remote_dir_exists(self, resource, _from, _to, use_sudo=False):
        # NOTE(jnowak): it's not efficient way to do so, but also this
        # transport is not that efficient
        if os.path.isdir(_from):
            r_dir_path = _to
        else:
            r_dir_path = _to.rsplit('/', 1)[0]
        self.other(resource).run(resource,
                                 'mkdir',
                                 '-p',
                                 r_dir_path,
                                 use_sudo=use_sudo)

    def _copy_file(self, resource, _from, _to, use_sudo=False):
        def wrp(transport):
            self._ensure_remote_dir_exists(resource, _from, _to, use_sudo)
            return fabric_project.put(
                remote_path=_to,
                local_path=_from,
                use_sudo=use_sudo
            )
        return wrp

    def _copy_directory(self, resource, _from, _to, use_sudo=False):
        def wrp(transport):
            self._ensure_remote_dir_exists(resource, _from, _to, use_sudo)
            return fabric_project.upload_project(
                remote_dir=_to,
                local_dir=_from,
                use_sudo=use_sudo
            )
        return wrp

    def copy(self, resource, _from, _to, use_sudo=False):
        log.debug('SCP: %s -> %s', _from, _to)

        if os.path.isfile(_from):
            executor = self._copy_file(resource, _from, _to, use_sudo)
        else:
            executor = self._copy_directory(resource, _from, _to, use_sudo)

        executor = ExecutorForFabric(resource=resource,
                                     executor=executor,
                                     params=(_from, _to, use_sudo))
        self.executors.append(executor)

    def run_all(self):
        for executor in self.executors:
            resource = executor.resource
            with fabric_api.settings(
                    abort_exception=executor._abort_exception,
                    **self.settings(resource)
            ):
                executor.run(self)


class SSHRunTransport(RunTransport, _SSHTransport):

    preffered_transport_name = 'ssh'

    def get_result(self, output):
        """Needed for compatibility with other handlers / transports"""
        return SolarTransportResult.from_fabric(output)

    def run(self, resource, *args, **kwargs):
        log.debug('SSH: %s', args)

        executor = fabric_api.run
        if kwargs.get('use_sudo', False):
            executor = fabric_api.sudo

        managers = [
            fabric_api.settings(**self.settings(resource)),
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
            res = executor(' '.join(args))
            return self.get_result(res)
