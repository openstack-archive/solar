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

from solar.orchestration.runner import app
from solar.system_log.operations import move_to_commited
from solar.system_log.operations import set_error

__all__ = ['error_logitem', 'commit_logitem']


@app.task(name='error_logitem')
def error_logitem(task_uuid):
    return set_error(task_uuid.rsplit(':', 1)[-1])


@app.task(name='commit_logitem')
def commit_logitem(task_uuid):
    return move_to_commited(task_uuid.rsplit(':', 1)[-1])
