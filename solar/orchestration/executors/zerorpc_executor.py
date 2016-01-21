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

import sys

import gevent
import zerorpc

from solar.core.log import log


class PoolBasedPuller(zerorpc.Puller):
    """ImprovedPuller allows to control pool of gevent threads and
    track assignments of gevent threads
    """
    def __init__(self, pool_size=100, *args, **kwargs):
        # TODO put pool_size into config for each worker
        self._tasks_pool = gevent.pool.Pool(pool_size)
        super(PoolBasedPuller, self).__init__(*args, **kwargs)

    def _receiver(self):
        while True:
            event = self._events.recv()
            self._handle_event(event)

    def _handle_event(self, event):
        self._tasks_pool.spawn(self._async_event, event)

    def _async_event(self, event):
        try:
            if event.name not in self._methods:
                raise NameError(event.name)
            self._context.hook_load_task_context(event.header)
            self._context.hook_server_before_exec(event)
            self._methods[event.name](*event.args)
            # In Push/Pull their is no reply to send, hence None for the
            # reply_event argument
            self._context.hook_server_after_exec(event, None)
        except Exception:
            exc_infos = sys.exc_info()
            try:
                log.exception('')
                self._context.hook_server_inspect_exception(
                    event, None, exc_infos)
            finally:
                del exc_infos

    def run(self):
        try:
            super(PoolBasedPuller, self).run()
        finally:
            self._tasks_pool.join(raise_error=True)


class LimitedExecutionPuller(PoolBasedPuller):

    def _handle_event(self, event):
        ctxt = event.args[0]
        timelimit = ctxt.get('timelimit', 0)
        if timelimit and 'kill' in self._methods:
            # greenlet for interupting pool-based greenlets shouldn't
            # share a pool with them, or it is highly possible that
            # it wont be ever executed with low number of greenlets in
            # a pool
            gevent.spawn_later(
                timelimit, self._methods['kill'], ctxt, ctxt['task_id'])
        self._tasks_pool.spawn(self._async_event, event)


class Executor(object):

    def __init__(self, worker, bind_to):
        self.worker = worker
        self.bind_to = bind_to
        self._tasks_register = {}
        worker._executor = self

    def register(self, ctxt):
        if 'task_id' in ctxt:
            self._tasks_register[ctxt['task_id']] = gevent.getcurrent()

    def kill(self, task_id, exc):
        if task_id in self._tasks_register:
            log.debug('Killing task %s', task_id)
            self._tasks_register[task_id].kill(exc, block=True)
            self._tasks_register.pop(task_id)

    def run(self):
        server = LimitedExecutionPuller(methods=self.worker)
        server.bind(self.bind_to)
        server.run()


class Client(object):

    def __init__(self, connect_to):
        self.connect_to = connect_to
        self.client = zerorpc.Pusher()
        self.client.connect(connect_to)

    def __getattr__(self, method):
        return getattr(self.client, method)

    def __call__(self, method, ctxt, *args, **kwargs):
        return getattr(self.client, method)(ctxt, *args, **kwargs)
