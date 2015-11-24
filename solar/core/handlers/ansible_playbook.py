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

from ansible.playbook import PlayBook
from ansible import utils
from ansible import callbacks
import ansible.constants as C
from fabric import api as fabric_api

from solar.core.log import log
from solar.core.handlers import base
from solar import errors
from solar.core.provider import SVNProvider

ROLES_PATH = '/etc/ansible/roles'


class AnsiblePlaybook(base.BaseHandler):

    def download_roles(self, urls):
        if not os.path.exists(ROLES_PATH):
            os.makedirs(ROLES_PATH)
        for url in urls:
            provider = SVNProvider(url)
            provider.run()
            fabric_api.local('cp -r {} {}'.format(
                provider.directory, ROLES_PATH))

    def action(self, resource, action):
        # This would require to put this file to remote and execute it (mostly)
        log.debug("Ansible playbook is not ported to pluggable transports")
        action_file = os.path.join(
            resource.metadata['actions_path'],
            resource.metadata['actions'][action])
        stats = callbacks.AggregateStats()
        playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
        runner_cb = callbacks.PlaybookRunnerCallbacks(stats, verbose=utils.VERBOSITY)

        variables = resource.args_dict()
        if 'roles' in variables:
            self.download_roles(variables['roles'])

        remote_user = variables.get('ssh_user') or C.DEFAULT_REMOTE_USER
        private_key_file = variables.get('ssh_key') or C.DEFAULT_PRIVATE_KEY_FILE
        if variables.get('ip'):
            host = variables['ip']
            transport = C.DEFAULT_TRANSPORT
        else:
            host = 'localhost'
            transport = 'local'
        C.HOST_KEY_CHECKING = False
        play = PlayBook(
            playbook=action_file,
            remote_user=remote_user,
            host_list=[host],
            private_key_file=private_key_file,
            extra_vars=variables,
            callbacks=playbook_cb,
            runner_callbacks=runner_cb,
            stats=stats,
            transport=transport)

        play.run()
        summary = stats.summarize(host)

        if summary.get('unreachable') or summary.get('failures'):
            raise errors.SolarError(
                'Ansible playbook %s failed with next summary %s',
                action_file, summary)
