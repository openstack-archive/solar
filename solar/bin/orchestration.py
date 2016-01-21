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


def run():

    import sys

    from gevent import joinall
    from gevent import spawn

    from solar.config import C
    from solar.core.log import log
    from solar.orchestration import construct_scheduler
    from solar.orchestration import construct_system_log
    from solar.orchestration import construct_tasks

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


def main():
    import daemonize

    from solar.config import C

    daem = daemonize.Daemonize(
        C.appname, C.pidfile, action=run)
    daem.start()
