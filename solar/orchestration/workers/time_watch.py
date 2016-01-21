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

from solar.core.log import log
from solar.orchestration.workers import base


class TimeWatcher(base.Worker):

    def __init__(self, tasks, scheduler):
        self.tasks = tasks
        self.scheduler = scheduler

    def timelimit(self, ctxt, task_id, limit):
        """Send kill message to tasks worker, and timeout message
        should be sent by tasks worker if task was killed
        """
        time.sleep(limit)
        log.debug('Sending kill request %s', task_id)
        self.tasks.kill(ctxt, task_id)
