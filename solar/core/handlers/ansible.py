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


import json
import os
import shutil
import tempfile

from solar.core.handlers.base import SOLAR_TEMP_LOCAL_LOCATION
from solar.core.handlers.base import TempFileHandler
from solar.core.log import log
from solar.core.provider import SVNProvider
from solar.core.transports.base import find_named_transport

ROLES_PATH = '/etc/ansible/roles'


class AnsibleHandlerBase(TempFileHandler):

    def download_roles(self, urls):
        if not os.path.exists(ROLES_PATH):
            os.makedirs(ROLES_PATH)
        for url in urls:
            provider = SVNProvider(url)
            provider.run()
            shutil.copytree(provider.directory, ROLES_PATH)

    def adjust_path(self, path):
        return path

    def _copy_ansible_library(self, resource):
        base_path = resource.db_obj.base_path
        src_ansible_library_dir = os.path.join(base_path, 'ansible_library')
        trg_ansible_library_dir = None
        if os.path.exists(src_ansible_library_dir):
            log.debug("Adding ansible_library for %s", resource.name)
            trg_ansible_library_dir = os.path.join(
                self.dirs[resource.name], 'ansible_library')
            shutil.copytree(src_ansible_library_dir, trg_ansible_library_dir)
        return trg_ansible_library_dir

    def _make_all(self, resource, action, action_path):
        dir_path = self.dirs[resource.name]

        playbook_file = self._make_playbook(resource, action, action_path)

        inventory_path = os.path.join(dir_path, 'inventory')
        with open(inventory_path, 'w') as inv:
            inv.write(self._make_inventory(resource))

        extra_vars_path = os.path.join(dir_path, 'extra_vars')
        with open(extra_vars_path, 'w') as extra:
            extra.write(self._make_extra_vars(resource))

        return playbook_file, inventory_path, extra_vars_path

    def _make_playbook(self, resource, action, action_path):
        dir_path = self.dirs[resource.name]
        dest_file = tempfile.mkstemp(text=True, prefix=action, dir=dir_path)[1]
        shutil.copyfile(action_path, dest_file)
        return dest_file

    def _make_inventory(self, resource):
        raise NotImplementedError()

    def _make_extra_vars(self, resource):
        r_args = resource.args
        return json.dumps(r_args)

    def make_ansible_command(self, remote_playbook_file,
                             remote_inventory_file, remote_extra_vars_file,
                             ansible_library_path):
        if ansible_library_path:
            r_ansible_library_path = self.adjust_path(ansible_library_path)
            call_args = [
                'ansible-playbook',
                '--module-path',
                r_ansible_library_path,
                '-i',
                remote_inventory_file,
                '--extra-vars',
                '@%s' % remote_extra_vars_file,
                remote_playbook_file
            ]
        else:
            call_args = [
                'ansible-playbook',
                '-i',
                remote_inventory_file,
                '--extra-vars',
                '@%s' % remote_extra_vars_file,
                remote_playbook_file
            ]
        return call_args

    def prepare(self, resource, action):
        action_file = os.path.join(
            resource.db_obj.actions_path,
            resource.actions[action])

        self._copy_templates_and_scripts(resource, action)
        ansible_library_path = self._copy_ansible_library(resource)
        files = self._make_all(resource,
                               action,
                               action_file)
        playbook_file, inventory_file, extra_vars_file = files

        remote_playbook_file = self.adjust_path(playbook_file)
        remote_inventory_file = self.adjust_path(inventory_file)
        remote_extra_vars_file = self.adjust_path(extra_vars_file)

        # TODO: clarify this for ansible template handler
        variables = resource.args
        if 'roles' in variables:
            self.download_roles(variables['roles'])

        call_args = self.make_ansible_command(remote_playbook_file,
                                              remote_inventory_file,
                                              remote_extra_vars_file,
                                              ansible_library_path)
        log.debug('Prepared ansible command: %s', ' '.join(call_args))
        return call_args

    def action(self, resource, action):
        raise NotImplementedError()


class AnsibleHandlerRemote(AnsibleHandlerBase):

    def adjust_path(self, path):
        return path.replace(SOLAR_TEMP_LOCAL_LOCATION, '/tmp/')

    def _make_inventory(self, resource):
        inventory = '{0} ansible_connection=local user={1}'
        user = self.transport_run.get_transport_data(resource)['user']
        host = 'localhost'
        return inventory.format(host, user)

    def prepare(self, resource, action):
        call_args = super(AnsibleHandlerRemote, self).prepare(resource, action)

        variables = resource.args
        if 'roles' in variables:
            self.transport_sync.copy(resource, ROLES_PATH, ROLES_PATH)

        self.transport_sync.copy(resource, self.dst, '/tmp')
        self.transport_sync.sync_all()
        return call_args


class AnsibleHandlerLocal(AnsibleHandlerBase):

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
