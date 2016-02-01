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
from solar.orchestration import extensions as loader
from solar.orchestration.executors import Executor
from solar.orchestration.workers.scheduler import SchedulerCallbackClient


SCHEDULER_CLIENT = loader.get_client('scheduler')


def construct_scheduler(extensions, clients):
    scheduler = extensions['scheduler']
    scheduler_executor = Executor(
        scheduler, clients['scheduler'].connect_to)
    scheduler.for_all.before(lambda ctxt: ModelMeta.session_start())
    scheduler.for_all.after(lambda ctxt: ModelMeta.session_end())
    scheduler_executor.run()


def construct_system_log(extensions, clients):
    syslog = extensions['system_log']
    syslog.for_all.before(lambda ctxt: ModelMeta.session_start())
    syslog.for_all.after(lambda ctxt: ModelMeta.session_end())
    Executor(syslog, clients['system_log'].connect_to).run()


def construct_tasks(extensions, clients):
    syslog = clients['system_log']
    # FIXME will be solved by hooks on certain events
    # solar.orchestraion.extensions.tasks.before =
    #   1 = solar.orchestration.workers.scheduler:subscribe
    scheduler = SchedulerCallbackClient(clients['scheduler'])
    tasks = extensions['tasks']
    tasks_executor = Executor(tasks, clients['tasks'].connect_to)
    tasks.for_all.before(tasks_executor.register_task)
    tasks.for_all.on_success(syslog.commit)
    tasks.for_all.on_error(syslog.error)
    tasks.for_all.on_success(scheduler.update)
    tasks.for_all.on_error(scheduler.error)
    tasks_executor.run()


def main():
    import sys
    from gevent import spawn
    from gevent import joinall
    clients = loader.get_clients()
    mgr = loader.get_extensions(clients)
    servers = [
        spawn(construct_scheduler, mgr, clients),
        spawn(construct_system_log, mgr, clients),
        spawn(construct_tasks, mgr, clients)
        ]
    try:
        log.info('Spawning scheduler, system log and tasks workers.')
        joinall(servers)
    except KeyboardInterrupt:
        log.info('Exit solar-worker')
        sys.exit()
