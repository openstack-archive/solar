

from solar.dblayer import ModelMeta
from solar.orchestration.workers.tasks import Tasks
from solar.orchestration.workers import scheduler as wscheduler
from solar.orchestration.workers.system_log import SystemLog
from solar.orchestration.executors.zerorpc_executor import Executor, Client

SYSLOG = 'ipc:///tmp/solar_system_log'
TASKS = 'ipc:///tmp/solar_tasks'
SCHEDULER = 'ipc:///tmp/solar_scheduler'

SCHEDULER_CLIENT = Client(SCHEDULER)


def construct_scheduler():
    scheduler = wscheduler.Scheduler(Client(TASKS))
    scheduler.for_all.before = ModelMeta.session_start
    scheduler.for_all.after = ModelMeta.session_end
    Executor(scheduler, SCHEDULER).run()


def construct_system_log():
    syslog = SystemLog()
    syslog.for_all.before = ModelMeta.session_start
    syslog.for_all.after = ModelMeta.session_end
    Executor(syslog, SYSLOG).run()


def construct_tasks():
    syslog = AsyncClient(SYSLOG)
    scheduler = wscheduler.SchedulerCallbackClient(
        AsyncClient(SCHEDULER))
    tasks = Tasks()
    tasks.for_all.on_success(syslog.commit)
    tasks.for_all.on_error(syslog.error)
    tasks.for_all.on_success(scheduler.update)
    tasks.for_all.on_error(scheduler.update)
    Executor(tasks, TASKS).run()


def main():
    import sys
    from gevent import spawn
    from gevent import joinall
    servers = [
        spawn(construct_scheduler),
        spawn(construct_system_log),
        spawn(construct_tasks)
        ]
    try:
        joinall(servers)
    except KeyboardInterrupt:
        print 'Exit solar-worker'
        sys.exit()
