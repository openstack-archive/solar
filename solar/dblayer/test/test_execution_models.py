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

from solar.dblayer.solar_models import Task


def test_tasks_selected_by_execution_id(rk):
    execution = next(rk)

    for i in range(2):
        t = Task.new({'name': str(i), 'execution': execution})
        t.save()
    another_execution = next(rk)

    for i in range(2):
        t = Task.new({'name': str(i), 'execution': another_execution})
        t.save()

    assert len(Task.execution.filter(execution)) == 2
    assert len(Task.execution.filter(another_execution)) == 2


def test_parent_child(rk):
    execution = next(rk)

    t1 = Task.new({'name': '1', 'execution': execution})

    t2 = Task.new({'name': '2', 'execution': execution})
    t1.childs.add(t2)
    t1.save()
    t2.save()

    assert Task.childs.filter(t1.key) == [t2.key]
    assert Task.parents.filter(t2.key) == [t1.key]
    assert t1.childs.all_tasks() == [t2]
    assert t2.parents.all_names() == [t1.name]
