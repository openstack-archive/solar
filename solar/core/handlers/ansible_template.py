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

from solar.core.handlers.ansible import AnsibleHandlerRemote
from solar.core.log import log


class AnsibleTemplate(AnsibleHandlerRemote):

    def _make_playbook(self, resource, action, action_path):
        return self._compile_action_file(resource, action)

    def action(self, resource, action):
        call_args = self.prepare(resource, action)
        log.debug('EXECUTING: %s', ' '.join(call_args))

        rst = self.transport_run.run(resource, *call_args)
        self.verify_run_result(call_args, rst)

    def _make_args(self, resource):
        args = super(AnsibleTemplate, self)._make_args(resource)
        args['host'] = 'localhost'
        return args
