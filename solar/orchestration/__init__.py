

from solar.dblayer import ModelMeta
from solar.orchestration.workers.tasks import Tasks
from solar.orchestration.workers.scheduler import Scheduler
from solar.orchestration.workers.system_log import SystemLog
from solar.orchestration.executors.zerorpc_executor import AsyncClient, Executor, Client


def construct_scheduler():
    scheduler = Scheduler(Client('ipc:///tmp/tasks'))
    scheduler.for_all.before = ModelMeta.session_start
    scheduler.for_all.after = ModelMeta.session_end
    Executor(scheduler, 'ipc:///tmp/scheduler').run()


def construct_system_log():
    syslog = SystemLog()
    syslog.for_all.before = ModelMeta.session_start
    syslog.for_all.after = ModelMeta.session_end
    Executor(syslog, 'ipc:///tmp/system_log').run()


def construct_tasks():
    syslog = AsyncClient('ipc:///tmp/syslog')
    scheduler = AsyncClient('ipc:///tmp/scheduler')
    tasks = Tasks()
    # tasks.for_all.on_success(syslog.commit)
    # tasks.for_all.on_error(syslog.error)
    tasks.for_all.on_success(scheduler.update_next)
    tasks.for_all.on_error(scheduler.update_next)
    Executor(tasks, 'ipc:///tmp/tasks').run()


def main():
    from gevent import spawn
    from gevent import joinall
    servers = [
        spawn(construct_scheduler),
        # spawn(construct_system_log),
        spawn(construct_tasks)
        ]
    try:
        joinall(servers)
    except KeyboardInterrupt:
        print 'Exit solar-worker'
