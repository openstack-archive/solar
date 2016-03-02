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
from solar.core.resource.resource import load
from solar.core.resource.resource import load_by_names
from solar import errors


class Executor(object):

    def __init__(self, resource, executor, params=None):
        """Executor

        :param resource: solar resource
        :param executor: callable executor, that will perform action
        :param params: optional argument
                       that migth be used later for decomposition etc
        """
        self.resource = resource
        self.params = params
        self._executor = executor
        self._valid = True

    @property
    def valid(self):
        return self._valid

    @valid.setter
    def valid(self, value):
        self._valid = value

    def run(self, transport):
        if self.valid:
            executor_result = self._executor(transport)
            if isinstance(executor_result, tuple) \
               and len(executor_result) == 3:
                # TODO Include file information in result
                obj = SolarTransportResult.from_tuple(*executor_result)
                log.debug(
                    'RC %s OUT %s ERR %s',
                    obj.return_code,
                    obj.stdout,
                    obj.stderr
                )
                if obj.success is False:
                    raise errors.SolarError(obj.output)
                elif obj.success is None:
                    log.debug("Cannot verify result")
            elif executor_result is None:
                pass
            else:
                log.debug("Unknown executor_result %r", executor_result)


class SolarTransportResult(object):

    def __init__(self):
        self.return_code = None
        self.stderr = None
        self.stdout = None

    @property
    def success(self):
        if self.return_code is not None:
            return self.return_code == 0
        return None

    @property
    def output(self):
        if self.success:
            return self.stdout
        msg = self.stderr
        if not msg:
            msg = self.stdout
        return msg

    @classmethod
    def from_tuple(cls, return_code, stdout, stderr):
        obj = cls()
        obj.return_code = return_code
        obj.stdout = stdout
        obj.stderr = stderr
        return obj

    def from_fabric(cls, fabric_obj):
        obj = cls()
        obj.return_code = fabric_obj['return_code']
        obj.stdout = fabric_obj['stdout']
        obj.stderr = fabric_obj['stderr']
        return obj


def find_named_transport(resource, req_name):
    transport = next(x for x in resource.transports()
                     if x['name'] == req_name)
    return transport


def locate_named_transport_resoruce(resource, name):
    transports = resource.db_obj.inputs._get_field_val('transports_id',
                                                       other='_key')
    transports_resource = load(transports)
    connections = transports_resource.connections
    just_names = filter(lambda x: x[1] == 'name', connections)
    transports = load_by_names([x[0] for x in just_names])
    transport = next(x for x in transports
                     if x.db_obj.inputs._get_raw_field_val('name') == name)
    return transport


class SolarTransport(object):

    _mode = None

    _priority = -1  # for priority ordering, high to low

    def __init__(self):
        pass

    def get_transport_data(self, resource, name=None):
        key = '_used_transport_%s' % self._mode
        # TODO: naive object local cache
        try:
            transport = getattr(resource, key)
        except AttributeError:
            if name is None:
                name = self.preffered_transport_name
            transport = next(x for x in resource.transports()
                             if x['name'] == name)
            setattr(resource, key, transport)
        return transport

    def other(self, resource):
        return self._other

    def bind_with(self, other):
        self._other = other


class SyncTransport(SolarTransport):
    """Transport that is responsible for file / directory syncing."""

    preffered_transport_name = None
    # NOTE(jnowak): reserved `supports_attrs` API for future use
    supports_attrs = False
    _mode = 'sync'

    def __init__(self):
        super(SyncTransport, self).__init__()
        self.executors = []

    def copy(self, resource, *args, **kwargs):
        pass

    def preprocess(self, executor):
        # we can check there if we need to run sync executor or not
        # ideally would be to do so on other side
        # it may set executor.valid to False then executor will be skipped
        pass

    def preprocess_all(self):
        # we cat use there md5 for big files to check if we need to sync it
        #   or if remote is still valid
        # we can run that in parallell also
        # can be also used to prepare files for further transfer
        for executor in self.executors:
            self.preprocess(executor)

    def apply_attrs(self):
        cmds = []
        single_res = self.executors[0].resource
        for executor in self.executors:
            _from, _to, use_sudo, args = executor.params
            if args.get('group') and args.get('owner'):
                cmds.append((use_sudo, 'chown {}:{} {}'.format(args['owner'],
                                                               args['group'],
                                                               _to)))
            elif args.get('group'):
                cmds.append((use_sudo, 'chgrp {} {}'.format(args['group'],
                                                            _to)))
            elif args.get('owner'):
                cmds.append((use_sudo, 'chown {} {}'.format(args['owner'],
                                                            _to)))
            elif args.get('permissions'):
                if os.path.isdir(_from):
                    cmds.append((use_sudo, 'chmod {} {}'.format(
                        args['permissions'],
                        _to
                    )))
                elif os.path.isfile(_from):
                    cmds.append((use_sudo, 'chmod {} {}'.format(
                        args['permissions'],
                        _to)))
        sudo_cmds = map(lambda (s, c): c if s else None, cmds)
        non_sudo_cmds = map(lambda (s, c): c if not s else None, cmds)
        sudo_cmds = filter(None, sudo_cmds)
        non_sudo_cmds = filter(None, non_sudo_cmds)
        if sudo_cmds:
            sudo_cmd = ' && '.join(sudo_cmds)
        else:
            sudo_cmd = None
        if non_sudo_cmds:
            non_sudo_cmd = ' && '.join(non_sudo_cmds)
        else:
            non_sudo_cmd = None
        # resource will be the same for all executors
        if sudo_cmd:
            self.other(single_res).run(
                single_res,
                sudo_cmd,
                use_sudo=True
            )
        if non_sudo_cmd:
            self.other(single_res).run(
                single_res,
                non_sudo_cmd,
                use_sudo=False
            )

    def run_all(self):
        for executor in self.executors:
            executor.run(self)
        if not self.supports_attrs:
            self.apply_attrs()

    def sync_all(self):
        """Syncs all

        It checks if action is required first,
        then runs all sequentially.
        Could be someday changed to parallel thing.
        """
        self.preprocess_all()
        self.run_all()
        self.executors = []  # clear after all


class RunTransport(SolarTransport):
    """Transport that is responsible for executing remote commands,

    rpc like thing
    """

    preffered_transport_name = None
    _mode = 'run'

    def __init__(self):
        super(RunTransport, self).__init__()

    def get_result(self, *args, **kwargs):
        raise NotImplementedError()

    def run(self, resource, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)
