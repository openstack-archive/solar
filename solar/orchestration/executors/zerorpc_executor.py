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

import zerorpc

from functools import partial


class Executor(object):

    def __init__(self, worker, bind_to):
        self.worker = worker
        self.bind_to = bind_to

    def run(self):
        server = zerorpc.Server(methods=self.worker)
        server.bind(self.bind_to)
        server.run()


class Client(object):

    def __init__(self, connect_to):
        self.connect_to = connect_to
        self.client = zerorpc.Client()
        self.client.connect(connect_to)

    def __getattr__(self, method):
        return getattr(self.client, method)

    def __call__(self, method, ctxt, *args, **kwargs):
        return getattr(self.client, method)(ctxt, *args, **kwargs)


class AsyncClient(object):

    def __init__(self, connect_to):
        self.connect_to = connect_to
        self.client = zerorpc.Client()
        self.client.connect(connect_to)

    def __call__(self, method, ctxt, *args, **kwargs):
        kwargs['async'] = True
        return getattr(self.client, method)(ctxt, *args, **kwargs)

    def __getattr__(self, method):
        return partial(getattr(self.client, method), async=True)
