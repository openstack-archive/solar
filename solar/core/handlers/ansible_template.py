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

from fabric.state import env
import os

import shutil
from solar.core.handlers.base import SOLAR_TEMP_LOCAL_LOCATION
from solar.core.handlers.base import TempFileHandler
from solar.core.log import log

# otherwise fabric will sys.exit(1) in case of errors
env.warn_only = True


class AnsibleTemplateBase(TempFileHandler):

    def _create_inventory(self, r):
        directory = self.dirs[r.name]
        inventory_path = os.path.join(directory, 'inventory')
        with open(inventory_path, 'w') as inv:
            inv.write(self._render_inventory(r))
        return inventory_path

    def _render_inventory(self, r):
        inventory = '{0} ansible_connection=local user={1} {2}'
        user = self.transport_run.get_transport_data(r)['user']
        host = 'localhost'
        args = []
        for arg in r.args:
            args.append('{0}="{1}"'.format(arg, r.args[arg]))
        args = ' '.join(args)
        inventory = inventory.format(host, user, args)
        log.debug(inventory)
        return inventory

    def _create_playbook(self, resource, action):
        return self._compile_action_file(resource, action)

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


# if we would have something like solar_agent that would render this then
# we would not need to render it there
# for now we redender it locally, sync to remote, run ansible on remote
# host as local
class AnsibleTemplate(AnsibleTemplateBase):

    def action(self, resource, action_name):
        inventory_file = self._create_inventory(resource)
        playbook_file = self._create_playbook(resource, action_name)
        log.debug('inventory_file: %s', inventory_file)
        log.debug('playbook_file: %s', playbook_file)

        self._copy_templates_and_scripts(resource, action_name)
        ansible_library_path = self._copy_ansible_library(resource)
        self.transport_sync.copy(resource, self.dst, '/tmp')
        self.transport_sync.sync_all()

        # remote paths are not nested inside solar_local
        remote_playbook_file = playbook_file.replace(
            SOLAR_TEMP_LOCAL_LOCATION, '/tmp/')
        remote_inventory_file = inventory_file.replace(
            SOLAR_TEMP_LOCAL_LOCATION, '/tmp/')

        if ansible_library_path:
            remote_ansible_library_path = ansible_library_path.replace(
                SOLAR_TEMP_LOCAL_LOCATION, '/tmp/')
            call_args = [
                'ansible-playbook',
                '--module-path',
                remote_ansible_library_path,
                '-i',
                remote_inventory_file,
                remote_playbook_file
            ]
        else:
            call_args = [
                'ansible-playbook',
                '-i',
                remote_inventory_file,
                remote_playbook_file
            ]
        log.debug('EXECUTING: %s', ' '.join(call_args))

        rst = self.transport_run.run(resource, *call_args)
        self.verify_run_result(call_args, rst)

    def _make_args(self, resource):
        args = super(AnsibleTemplate, self)._make_args(resource)
        args['host'] = 'localhost'
        return args
