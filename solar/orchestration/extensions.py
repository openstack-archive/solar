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

from functools import partial

from stevedore import driver
from stevedore import extension

from solar.config import C
from solar.orchestration.executors import Client


def client(address):
    return Client(address)


tasks_client = partial(client, C.tasks_address)
scheduler_client = partial(client, C.scheduler_address)
system_log_client = partial(client, C.system_log_address)


def get_driver(extension, implementation):
    mgr = driver.DriverManager(
        namespace='solar.orchestration.drivers.%s' % extension,
        name=implementation,
        invoke_on_load=False,
    )
    return mgr.driver


def tasks(clients):
    return get_driver('tasks', C.tasks_driver)()


def scheduler(clients):
    return get_driver('scheduler', C.scheduler_driver)(clients['tasks'])


def system_log(clients):
    return get_driver('system_log', C.system_log_driver)()


class GetObjExtensionManager(extension.ExtensionManager):

    def __getitem__(self, name):
        ext = super(GetObjExtensionManager, self).__getitem__(name)
        return ext.obj


def get_clients():
    return GetObjExtensionManager(
        namespace='solar.orchestration.extensions_clients',
        invoke_on_load=True)


def get_client(name):
    return get_clients()[name]


def get_extensions(clients):
    ext = GetObjExtensionManager(
        namespace='solar.orchestration.extensions',
        invoke_on_load=True,
        invoke_args=(clients,))
    return ext
