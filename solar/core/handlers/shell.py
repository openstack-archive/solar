# -*- coding: utf-8 -*-
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

from solar.core.handlers.base import SOLAR_TEMP_LOCAL_LOCATION
from solar.core.handlers.base import TempFileHandler
from solar.core.log import log


class Shell(TempFileHandler):

    def action(self, resource, action_name):
        action_file = self._compile_action_file(resource, action_name)
        log.debug('action_file: %s', action_file)

        action_file_name = os.path.join(self.dirs[resource.name], action_file)
        action_file_name = action_file_name.replace(
            SOLAR_TEMP_LOCAL_LOCATION, '/tmp/')

        self._copy_templates_and_scripts(resource, action_name)

        self.transport_sync.copy(resource, self.dst, '/tmp')
        self.transport_sync.sync_all()

        rst = self.transport_run.run(
            resource,
            'bash', action_file_name,
            use_sudo=True,
            warn_only=True
        )
        self.verify_run_results(['bash', action_file_name], rst)
