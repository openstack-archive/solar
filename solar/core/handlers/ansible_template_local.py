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


from solar.core.handlers.ansible_template import AnsibleTemplateBase
from solar.core.log import log
from solar import errors
from solar.utils import execute


class AnsibleTemplateLocal(AnsibleTemplateBase):

    def _make_args(self, resource):
        args = super(AnsibleTemplateLocal, self)._make_args(resource)
        return args

    def _render_inventory(self, r):
        ssh_transport = next(x for x in r.transports() if x['name'] == 'ssh')
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
        host = r.ip()
        user = ssh_transport['user']
        inventory = inventory.format(host, host, user, ssh_auth_data)
        log.debug(inventory)
        return inventory

    def action(self, resource, action_name):
        inventory_file = self._create_inventory(resource)
        playbook_file = self._create_playbook(resource, action_name)
        extra_vars_file = self._create_extra_vars(resource)

        log.debug('inventory_file: %s', inventory_file)
        log.debug('playbook_file: %s', playbook_file)

        lib_path = self._copy_ansible_library(resource)
        if lib_path:
            call_args = [
                'ansible-playbook',
                '--module-path',
                lib_path,
                '-i',
                inventory_file,
                '--extra-vars',
                '@%s' % extra_vars_file,
                playbook_file
            ]
        else:
            call_args = [
                'ansible-playbook',
                '-i',
                inventory_file,
                '--extra-vars',
                '@%s' % extra_vars_file,
                playbook_file
            ]
        log.debug('EXECUTING: %s', ' '.join(call_args))

        ret, out, err = execute(call_args)
        if ret == 0:
            return
        else:
            # ansible returns errors on stdout
            raise errors.SolarError(out)
