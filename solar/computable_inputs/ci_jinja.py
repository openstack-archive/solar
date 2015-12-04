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

from jinja2.sandbox import SandboxedEnvironment
from solar.computable_inputs import ComputableInputProcessor


def make_arr(data):
    t = {}
    for ov in data:
        if t.get(ov['resource']) is None:
            t[ov['resource']] = {}
        t[ov['resource']][ov['other_input']] = ov['value']
    return t


class JinjaProcessor(ComputableInputProcessor):

    def __init__(self):
        self.env = SandboxedEnvironment(trim_blocks=True,
                                        lstrip_blocks=True)
        self._globals = {'make_arr': make_arr}

    def run(self, resource_name, computable_type, funct, data):
        t = self.env.from_string(funct, globals=self._globals)
        return t.render(resource_name=resource_name, data=data).strip()
