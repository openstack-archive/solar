
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
