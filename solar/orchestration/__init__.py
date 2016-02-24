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

import argparse

from solar.config import C
from solar.core.log import log
from solar.dblayer import ModelMeta
from solar.orchestration.executors import Executor
from solar.orchestration import extensions as loader


SCHEDULER_CLIENT = loader.get_client('scheduler')


def wrap_session(extension, clients):
    log.debug('DB session for %r', extension)
    extension.for_all.before(lambda ctxt: ModelMeta.session_start())
    extension.for_all.after(lambda ctxt: ModelMeta.session_end())


def construct_scheduler(extensions, clients):
    scheduler = extensions['scheduler']
    loader.load_contruct_hooks('scheduler', extensions, clients)
    scheduler_executor = Executor(
        scheduler, clients['scheduler'].connect_to)
    scheduler_executor.run()


def construct_system_log(extensions, clients):
    syslog = extensions['system_log']
    loader.load_contruct_hooks('system_log', extensions, clients)
    Executor(syslog, clients['system_log'].connect_to).run()


def construct_tasks(extensions, clients):
    tasks = extensions['tasks']
    loader.load_contruct_hooks('tasks', extensions, clients)
    tasks_executor = Executor(tasks, clients['tasks'].connect_to)
    tasks.for_all.before(tasks_executor.register_task)
    tasks_executor.run()


def main():
    # NOTE(mkwiek): no arguments should be supplied to solar-worker
    argparse.ArgumentParser().parse_args()
    runner = loader.get_runner(C.runner)
    constructors = loader.get_constructors()
    clients = loader.get_clients()
    exts = loader.get_extensions(clients)
    runner.driver(constructors, exts, clients)
