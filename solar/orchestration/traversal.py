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

"""

task should be visited only when predecessors are visited,
visited node could be only in SUCCESS or ERROR

task can be scheduled for execution if it is not yet visited, and state
not in SKIPPED, INPROGRESS

PENDING - task that is scheduled to be executed
ERROR_RETRY - task was in error but will be re-executed
ERROR - visited node, but failed, can be failed by timeout
SUCCESS - visited node, successfull
INPROGRESS - task already scheduled, can be moved to ERROR or SUCCESS
SKIPPED - not visited, and should be skipped from execution
NOOP - task wont be executed, but should be treated as visited
"""

from enum import Enum

states = Enum(
    'States',
    'SUCCESS ERROR NOOP INPROGRESS SKIPPED PENDING ERROR_RETRY')

VISITED = (states.SUCCESS.name, states.NOOP.name)
BLOCKED = (states.INPROGRESS.name, states.SKIPPED.name, states.ERROR.name)


def find_visitable_tasks(dg):
    """Filter to find tasks that satisfy next conditions:
    - task is not in VISITED or BLOCKED state
    - all predecessors of task can be considered visited
    """
    visited = set([t for t in dg if t.status in VISITED])
    return [t for t in dg
            if (not (t in visited or t.status in BLOCKED)
                and set(dg.predecessors(t)) <= visited)]
