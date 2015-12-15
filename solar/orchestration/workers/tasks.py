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

import sys
import time

from solar.orchestration.workers import base
from solar.core.log import log
from solar.core import resource
from solar.core import actions


class Tasks(base.Worker):

    def sleep(self, ctxt, seconds):
        return time.sleep(seconds)

    def error(self, ctxt, message):
        raise Exception(message)

    def echo(self, ctxt, message):
        return message

    def solar_resource(self, ctxt, resource_name, action):
        log.debug('TASK solar resource NAME %s ACTION %s',
                  resource_name, action)
        res = resource.load(resource_name)
        return actions.resource_action(res, action)


def run(bind_to):
    from solar.orchestration.executors import zerorpc_executor
    zerorpc_executor.Executor(Tasks(), bind_to).run()


def client(connect_to):
    from solar.orchestration.executors import zerorpc_executor
    return zerorpc_executor.Client(connect_to)
