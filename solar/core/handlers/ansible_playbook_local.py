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

from solar import errors

from solar.core.handlers.ansible_playbook import AnsiblePlaybookBase
from solar.core.log import log
from solar.core.transports.base import find_named_transport
from solar.utils import execute


class AnsiblePlaybookLocal(AnsiblePlaybookBase):

    def _make_inventory(self, resource):
        ssh_transport = find_named_transport(resource, 'ssh')
        ssh_key = ssh_transport.get('key')
        ssh_password = ssh_transport.get('password')

        if ssh_key:
            inventory = '{0} ansible_ssh_host={1} ansible_connection=ssh \
            ansible_ssh_user={2} ansible_ssh_private_key_file={3}'
            ssh_auth_data = ssh_key
        elif ssh_password:
            inventory = '{0} ansible_ssh_host={1} \
            ansible_ssh_user={2} ansible_ssh_pass={3}'
            ssh_auth_data = ssh_password
        else:
            raise Exception("No key and no password given")
        user = ssh_transport['user']
        host = resource.ip()
        return inventory.format(host, host, user, ssh_auth_data)

    def action(self, resource, action):

        action_file = os.path.join(
            resource.db_obj.actions_path,
            resource.actions[action])

        files = self._make_playbook(resource,
                                    action,
                                    action_file)
        playbook_file, inventory_file, extra_vars_file = files

        variables = resource.args
        if 'roles' in variables:
            self.download_roles(variables['roles'])

        ansible_library_path = self._copy_ansible_library(resource)
        call_args = self.make_ansible_command(playbook_file,
                                              inventory_file,
                                              extra_vars_file,
                                              ansible_library_path)

        log.debug('EXECUTING: %s', ' '.join(call_args))

        ret, out, err = execute(call_args)
        if ret == 0:
            return
        else:
            raise errors.SolarError(out)
