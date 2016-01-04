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

# this has to be before callbacks, otherwise ansible circural import problem
from ansible import utils

# intentional line, otherwise H306
from ansible import callbacks

import ansible.constants as C
from ansible.playbook import PlayBook

from solar.core.transports.base import find_named_transport
from solar import errors

from solar.core.handlers.ansible_playbook import AnsiblePlaybookBase


class AnsiblePlaybookLocal(AnsiblePlaybookBase):

    def action(self, resource, action):
        # This would require to put this file to remote and execute it (mostly)

        ssh_props = find_named_transport(resource, 'ssh')

        remote_user = ssh_props['user']
        private_key_file = ssh_props.get('key')
        ssh_password = ssh_props.get('password')

        action_file = os.path.join(
            resource.db_obj.actions_path,
            resource.actions[action])

        variables = resource.args
        if 'roles' in variables:
            self.download_roles(variables['roles'])

        host = resource.ip()
        transport = C.DEFAULT_TRANSPORT

        C.HOST_KEY_CHECKING = False

        stats = callbacks.AggregateStats()
        playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
        runner_cb = callbacks.PlaybookRunnerCallbacks(
            stats, verbose=utils.VERBOSITY)

        opts = dict(
            playbook=action_file,
            remote_user=remote_user,
            host_list=[host],
            extra_vars=variables,
            callbacks=playbook_cb,
            runner_callbacks=runner_cb,
            stats=stats,
            transport=transport)

        if ssh_password:
            opts['remote_pass'] = ssh_password
        elif private_key_file:
            opts['private_key_file'] = private_key_file
        else:
            raise Exception("No key and no password given")

        play = PlayBook(**opts)

        play.run()
        summary = stats.summarize(host)

        if summary.get('unreachable') or summary.get('failures'):
            raise errors.SolarError(
                'Ansible playbook %s failed with next summary %s',
                action_file, summary)
