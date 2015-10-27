import pytest

from solar.dblayer.solar_models import Task


def test_tasks_selected_by_execution_id(rk):
    execution = next(rk)

    for i in range(2):
        t = Task.from_dict(
            str(i)+execution,
            {'name': str(i),
             'execution': execution})
        t.save()
    another_execution = next(rk)

    for i in range(2):
        t = Task.from_dict(
            str(i)+another_execution,
            {'name': str(i),
             'execution': another_execution})
        t.save()

    assert len(Task.execution.filter(execution)) == 2
    assert len(Task.execution.filter(another_execution)) == 2


def test_parent_child(rk):
    execution = next(rk)

    t1 = Task.from_dict(
            '1'+execution,
            {'name': '1',
             'execution': execution})
    t1.save()
    t2 = Task.from_dict(
            '2'+execution,
            {'name': '2',
             'execution': execution})
    t2.save()

    t1.childs.add(t2)
