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


class Executor(object):

    def __init__(self, resource, executor, params=None):
        """
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
            self._executor(transport)


class SolarTransport(object):

    def __init__(self):
        pass

    def get_transport_data(self, resource, name=None):
        # TODO: naive object local cache
        try:
            transport = resource._used_transport
        except AttributeError:
            if name is None:
                name = self.preffered_transport_name
            transport = next(x for x in resource.transports() if x['name'] == name)
            setattr(resource, '_used_transport', transport)
        return transport



class SolarRunResult(object):

    def __init__(self, result, failed=False):
        self._result = result
        self._failed = failed

    @property
    def failed(self):
        return self._failed

    @property
    def result(self):
        return self._result


class SyncTransport(SolarTransport):
    """
    Transport that is responsible for file / directory syncing.
    """

    preffered_transport_name = None

    def __init__(self):
        super(SyncTransport, self).__init__()
        self.executors = []

    def bind_with(self, other):
        # we migth add there something later
        # like compat checking etc
        self.other = other

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

    def run_all(self):
        for executor in self.executors:
            executor.run(self)

    def sync_all(self):
        """
        It checks if action is required first,
        then runs all sequentially.
        Could be someday changed to parallel thing.
        """
        self.preprocess_all()
        self.run_all()
        self.executors = []  # clear after all


class RunTransport(SolarTransport):
    """
    Transport that is responsible for executing remote commands, rpc like thing.
    """

    preffered_transport_name = None

    def __init__(self):
        super(RunTransport, self).__init__()

    def get_result(self, *args, **kwargs):
        raise NotImplementedError()

    def bind_with(self, other):
        # we migth add there something later
        # like compat checking etc
        self.other = other

    def run(self, resource, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)
