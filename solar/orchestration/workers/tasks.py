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

import time

from solar.core import actions
from solar.core.log import log
from solar.core import resource
from solar.errors import ExecutionTimeout
from solar.orchestration.workers import base


class Tasks(base.Worker):

    def sleep(self, ctxt, seconds):
        log.debug('Received sleep for %s', seconds)
        time.sleep(seconds)
        log.debug('Finished sleep %s', seconds)
        return None

    def error(self, ctxt, message):
        raise Exception(message)

    def echo(self, ctxt, message):
        return message

    def solar_resource(self, ctxt, resource_name, action):
        log.debug('TASK solar resource NAME %s ACTION %s',
                  resource_name, action)
        res = resource.load(resource_name)
        return actions.resource_action(res, action)

    def kill(self, ctxt, task_id):
        log.debug('Received kill request for task_id %s', task_id)
        if not hasattr(self._executor, 'kill'):
            raise NotImplementedError(
                'Current executor doesnt support interruping tasks')
        self._executor.kill(task_id, ExecutionTimeout)
