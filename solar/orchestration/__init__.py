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

from solar.config import C
from solar.core.log import log
from solar.dblayer import ModelMeta
from solar.orchestration.executors import Client
from solar.orchestration.executors import Executor
from solar.orchestration.workers import scheduler as wscheduler
from solar.orchestration.workers.system_log import SystemLog
from solar.orchestration.workers.tasks import Tasks


SCHEDULER_CLIENT = Client(C.scheduler_address)


def construct_scheduler(tasks_address, scheduler_address):
    scheduler = wscheduler.Scheduler(Client(tasks_address))
    scheduler_executor = Executor(scheduler, scheduler_address)
    scheduler.for_all.before(lambda ctxt: ModelMeta.session_start())
    scheduler.for_all.after(lambda ctxt: ModelMeta.session_end())
    Executor(scheduler, scheduler_address).run()


def construct_system_log(system_log_address):
    syslog = SystemLog()
    syslog.for_all.before(lambda ctxt: ModelMeta.session_start())
    syslog.for_all.after(lambda ctxt: ModelMeta.session_end())
    Executor(syslog, system_log_address).run()


def construct_tasks(system_log_address, tasks_address, scheduler_address):
    syslog = Client(system_log_address)
    scheduler = wscheduler.SchedulerCallbackClient(
        Client(scheduler_address))
    tasks = Tasks()
    tasks_executor = Executor(tasks, tasks_address)
    tasks.for_all.before(tasks_executor.register_task)
    tasks.for_all.on_success(syslog.commit)
    tasks.for_all.on_error(syslog.error)
    tasks.for_all.on_success(scheduler.update)
    tasks.for_all.on_error(scheduler.error)
    Executor(tasks, tasks_address).run()


def main():
    import sys
    from gevent import spawn
    from gevent import joinall
    servers = [
        spawn(construct_scheduler, C.tasks_address, C.scheduler_address),
        spawn(construct_system_log, C.system_log_address),
        spawn(construct_tasks, C.system_log_address, C.tasks_address,
              C.scheduler_address)
        ]
    try:
        log.info('Spawning scheduler, system log and tasks workers.')
        joinall(servers)
    except KeyboardInterrupt:
        log.info('Exit solar-worker')
        sys.exit()
