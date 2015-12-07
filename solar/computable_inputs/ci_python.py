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


import json
import os
import struct
import subprocess

from solar.computable_inputs import ComputableInputProcessor
from solar.computable_inputs import ComputablePassedTypes
from solar.computable_inputs import HELPERS_PATH


_PYTHON_WORKER = os.path.join(HELPERS_PATH, 'python_loop.py')
_PYTHON_HELPERS = open(os.path.join(HELPERS_PATH, 'python_helpers.py')).read()


class Mgr(object):

    def __init__(self):
        self.child = None

    def run(self):
        self.child = subprocess.Popen(['/usr/bin/env', 'python',
                                       _PYTHON_WORKER],
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE)
        self.prepare()

    def prepare(self):
        self.run_code(fname=None,
                      code=_PYTHON_HELPERS,
                      kwargs={},
                      copy_env=False)

    def kill_child(self):
        self.child.kill()

    def ensure_running(self):
        if self.child is None:
            self.run()
        try:
            os.waitpid(self.child.pid, os.WNOHANG)
        except Exception:
            running = False
        else:
            running = True
        if not running:
            self.run()

    def send(self, data):
        c_data = json.dumps(data)
        dlen = len(c_data)
        self.ensure_running()
        self.child.stdin.write(struct.pack('<L', dlen))
        self.child.stdin.write(c_data)
        self.child.stdin.flush()

    def read(self):
        # TODO (jnowak) this int may be unsafe
        hdr = self.child.stdout.read(struct.calcsize('<L'))
        if not hdr:
            raise Exception("Loop crashed, probably invalid code")
        dlen = int(struct.unpack('<L', hdr)[0])
        data = self.child.stdout.read(dlen)
        return json.loads(data)

    def run_code(self, fname, code, kwargs, copy_env=True):
        self.send({'fname': fname,
                   'code': code,
                   'kwargs': kwargs,
                   'copy_env': copy_env})
        result = self.read()
        if 'error' in result:
            raise Exception("Loop error: %r" % result['error'])
        return result['result']


class PyProcessor(ComputableInputProcessor):

    def __init__(self):
        self.mgr = Mgr()
        self.mgr.run()

    def check_funct(self, funct, computable_type):
        if not funct.startswith('def calculate_input('):
            code = funct.splitlines()
            if computable_type == ComputablePassedTypes.full.name:
                code.insert(0, 'R = make_arr(D)')
            code = '\n    '.join(code)
            return 'def calculate_input(D, resource_name):\n    %s' % code
        return funct

    def run(self, resource_name, computable_type, funct, data):
        funct = self.check_funct(funct, computable_type)
        value = self.mgr.run_code(code=funct,
                                  fname='calculate_input',
                                  kwargs={'D': data,
                                          'resource_name': resource_name})
        return value
