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

import json
import shutil
import tempfile

from solar.core.handlers import base
from solar.core.handlers.base import SOLAR_TEMP_LOCAL_LOCATION
from solar.core.handlers.base import TempFileHandler
from solar.core.log import log
from solar.core.provider import SVNProvider


ROLES_PATH = '/etc/ansible/roles'


class AnsiblePlaybookBase(base.BaseHandler):

    def download_roles(self, urls):
        if not os.path.exists(ROLES_PATH):
            os.makedirs(ROLES_PATH)
        for url in urls:
            provider = SVNProvider(url)
            provider.run()
            shutil.copytree(provider.directory, ROLES_PATH)


class AnsiblePlaybook(AnsiblePlaybookBase, TempFileHandler):

    def _make_playbook(self, resource, action, action_path):
        dir_path = self.dirs[resource.name]
        dest_file = tempfile.mkstemp(text=True, prefix=action, dir=dir_path)[1]

        shutil.copyfile(action_path, dest_file)

        inventory_path = os.path.join(dir_path, 'inventory')
        with open(inventory_path, 'w') as inv:
            inv.write(self._make_inventory(resource))

        extra_vars_path = os.path.join(dir_path, 'extra_vars')
        with open(extra_vars_path, 'w') as extra:
            extra.write(self._make_extra_vars(resource))

        return dest_file, inventory_path, extra_vars_path

    def _make_inventory(self, resource):
        inventory = '{0} ansible_connection=local user={1}'
        user = self.transport_run.get_transport_data(resource)['user']
        host = 'localhost'
        return inventory.format(host, user)

    def _make_extra_vars(self, resource):
        r_args = resource.args
        return json.dumps(r_args)

    def action(self, resource, action):
        action_file = os.path.join(
            resource.db_obj.actions_path,
            resource.actions[action])

        self.prepare_templates_and_scripts(resource, action)
        files = self._make_playbook(resource,
                                    action,
                                    action_file)
        playbook_file, inventory_file, extra_vars_file = files
        self.transport_sync.copy(resource, self.dst, '/tmp')

        variables = resource.args
        if 'roles' in variables:
            self.download_roles(variables['roles'])
            self.transport_sync.copy(resource, ROLES_PATH, ROLES_PATH)

        self.transport_sync.sync_all()

        remote_playbook_file = playbook_file.replace(
            SOLAR_TEMP_LOCAL_LOCATION, '/tmp/')
        remote_inventory_file = inventory_file.replace(
            SOLAR_TEMP_LOCAL_LOCATION, '/tmp/')
        remote_extra_vars_file = extra_vars_file.replace(
            SOLAR_TEMP_LOCAL_LOCATION, '/tmp/')

        call_args = ['ansible-playbook', '--module-path', '/tmp/library',
                     '-i', remote_inventory_file,
                     '--extra-vars', '@%s' % remote_extra_vars_file,
                     remote_playbook_file]
        log.debug('EXECUTING: %s', ' '.join(call_args))

        rst = self.transport_run.run(resource, *call_args)
        self.verify_run_result(call_args, rst)
