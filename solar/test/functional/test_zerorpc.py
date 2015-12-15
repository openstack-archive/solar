
import pytest


def test_scheduler_riak_plan(scheduler, tracer, riak_plan):
    scheduler('next', {}, riak_plan.graph['uid'])
    assert len(tracer.call_args_list) == 3
    task_args_list = set()
    for call in tracer.call_args_list:
        task_args_list.add(tuple(call[0][2]))
    assert {('node1', 'run'), ('node2', 'run'), ('node3', 'run')} == task_args_list
    task_type, ctxt, args = tracer.call_args_list[0][0]
    tracer.reset_mock()
    scheduler('update_next', {}, ctxt['task_id'], 'SUCCESS')
    assert len(tracer.call_args_list) == 1
    task_type, ctxt, args = tracer.call_args_list[0][0]
    assert 'hosts_file' in args[0] and 'run' == args[1]


@pytest.mark.parametrize('message', ['hello1', 'hello2'])
def test_tasks_worker_echo(tasks, message):
    assert tasks('echo', {}, message, async=True).wait() == message


def test_tasks_worker_sleep(tasks):
    assert tasks('sleep', {}, 0.2) == None


def test_tasks_worker_error(tasks):
    with pytest.raises(Exception):
        assert tasks('error', {}, 'message')
