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

# Consider this part as POC

import json
import struct
import sys

_hdr_size = struct.calcsize('<L')

try:
    from seccomp import *  # noqa
except ImportError:
    # TODO: (jnowak) unsafe fallback for now
    pass
else:
    RULES = SyscallFilter(defaction=KILL)

    RULES.add_rule(ALLOW, 'read', Arg(0, EQ, sys.stdin.fileno()))
    RULES.add_rule(ALLOW, 'fstat')
    RULES.add_rule(ALLOW, 'mmap')
    RULES.add_rule(ALLOW, 'write', Arg(0, EQ, sys.stdout.fileno()))
    RULES.add_rule(ALLOW, "exit_group")
    RULES.add_rule(ALLOW, "rt_sigaction")
    RULES.add_rule(ALLOW, "brk")

    RULES.load()


_env = {}


def exec_remote(fname, code, kwargs, copy_env=True):
    if copy_env:
        local_env = _env.copy()
    else:
        local_env = _env
    local_env.update(**kwargs)
    exec code in _env
    if fname is not None:
        return _env[fname](**kwargs)
    return True


while True:
    read = sys.stdin.read(_hdr_size)
    if not read:
        break
    d_size = int(struct.unpack('<L', read)[0])
    data = sys.stdin.read(d_size)
    cmd = json.loads(data)
    result, error = None, None
    try:
        result = exec_remote(**cmd)
    except Exception as ex:
        error = str(ex)
    if result:
        resp = {'result': result}
    else:
        resp = {'error': error}
    resp_json = json.dumps(resp)
    sys.stdout.write(struct.pack("<L", len(resp_json)))
    sys.stdout.write(resp_json)
    sys.stdout.flush()
