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

from solar.core.log import log
from solar import errors

from solar.core.handlers.base import TempFileHandler


class Shell(TempFileHandler):
    def action(self, resource, action_name):
        action_file = self._compile_action_file(resource, action_name)
        log.debug('action_file: %s', action_file)

        self.transport_sync.copy(resource, action_file, '/tmp/action.sh')
        self.transport_sync.sync_all()
        cmd = self.transport_run.run(
            resource,
            'bash', '/tmp/action.sh',
            use_sudo=True,
            warn_only=True
        )

        if cmd.return_code:
            raise errors.SolarError(
                'Bash execution for {} failed with {}'.format(
                    resource.name, cmd.return_code))
        return cmd
