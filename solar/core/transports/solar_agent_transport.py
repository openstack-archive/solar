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


from solar_agent.client import SolarAgentClient

from solar.core.log import log
from solar.core.transports.base import Executor
from solar.core.transports.base import RunTransport
from solar.core.transports.base import SolarTransportResult
from solar.core.transports.base import SyncTransport


class SolarAgentTransport(object):

    _priority = 50

    def get_client(self, resource):
        transport = self.get_transport_data(resource)
        host = resource.ip()
        user = transport['user']
        port = transport['port']
        auth = transport['password']
        transport_class = transport.get('transport_class')
        client = SolarAgentClient(auth={'user': user, 'auth': auth},
                                  transport_args=(host, port),
                                  transport_class=transport_class)
        return client


class SolarAgentSyncTransport(SyncTransport, SolarAgentTransport):

    preffered_transport_name = 'solar_agent'

    def copy(self, resource, _from, _to, use_sudo=False):
        log.debug("SolarAgent copy: %s -> %s", _from, _to)

        client = self.get_client(resource)
        executor = lambda transport: client.copy(_from, _to, use_sudo)
        executor = Executor(resource=resource,
                            executor=executor,
                            params=(_from, _to, use_sudo))
        self.executors.append(executor)


class SolarAgentRunTransport(RunTransport, SolarAgentTransport):

    preffered_transport_name = 'solar_agent'

    def get_result(self, result):
        obj = SolarTransportResult()
        obj.return_code = result['return_code']
        obj.stderr = result['stderr']
        obj.stdout = result['stdout']
        return obj

    def run(self, resource, *args, **kwargs):
        log.debug("SolarAgent run: %s", args)
        client = self.get_client(resource)
        res = client.run(' '.join(args), **kwargs)
        return self.get_result(res)
