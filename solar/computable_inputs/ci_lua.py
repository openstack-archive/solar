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

import lupa
from lupa import LuaRuntime
from solar.computable_inputs import ComputableInputProcessor


class LuaProcessor(ComputableInputProcessor):

    def __init__(self):
        self.lua = LuaRuntime()

    def run(self, funct, data):
        if isinstance(data, list):
            lua_data = self.lua.table_from(data)
        else:
            lua_data = data
        funct_lua = self.lua.eval(funct)
        return funct_lua(lua_data)
