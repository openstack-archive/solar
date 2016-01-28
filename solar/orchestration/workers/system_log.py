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

from solar.core.log import log
from solar.orchestration.workers import base
from solar.system_log.operations import move_to_commited
from solar.system_log.operations import set_error


class SystemLog(base.Worker):

    def commit(self, ctxt, *args, **kwargs):
        return move_to_commited(ctxt['task_id'].rsplit(':', 1)[-1])

    def error(self, ctxt, *args, **kwargs):
        return set_error(ctxt['task_id'].rsplit(':', 1)[-1])


def tasks_subscribe(tasks, clients):
    log.debug('System log subscribes to tasks hooks')
    syslog = clients['system_log']
    tasks.for_all.on_success(syslog.commit)
    tasks.for_all.on_error(syslog.error)
