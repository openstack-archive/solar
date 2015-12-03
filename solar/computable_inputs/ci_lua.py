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


import os

from lupa import LuaRuntime
from solar.computable_inputs import ComputableInputProcessor
from solar.computable_inputs import HELPERS_PATH
from solar.dblayer.solar_models import ComputablePassedTypes


_LUA_HELPERS = open(os.path.join(HELPERS_PATH, 'lua_helpers.lua')).read()


# TODO: (jnowak) add sandoxing


class LuaProcessor(ComputableInputProcessor):

    def __init__(self):
        self.lua = LuaRuntime()
        self.lua.execute(_LUA_HELPERS)

    def run(self, computable_type, funct, data):
        # when computable_type == full then raw python object is passed
        # to lua (counts from 0 etc)

        if isinstance(data, list) \
           and computable_type == ComputablePassedTypes.values.name:
            lua_data = self.lua.table_from(data)
        else:
            lua_data = data

        funct_lua = self.lua.eval(funct)
        return funct_lua(lua_data)
