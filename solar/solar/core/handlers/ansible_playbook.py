# -*- coding: utf-8 -*-

import os

from ansible.playbook import PlayBook
from ansible import utils
from ansible import callbacks
import ansible.constants as C

from solar.core.handlers import base


class AnsiblePlaybook(base.BaseHandler):

    def action(self, resource, action):
        action_file = os.path.join(
            resource.metadata['actions_path'],
            resource.metadata['actions'][action])
        stats = callbacks.AggregateStats()
        playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
        runner_cb = callbacks.PlaybookRunnerCallbacks(stats, verbose=utils.VERBOSITY)

        variables = resource.args_dict()
        remote_user = variables.get('ssh_user') or C.DEFAULT_REMOTE_USER
        private_key_file = variables.get('ssh_key') or C.DEFAULT_PRIVATE_KEY_FILE
        if variables.get('ip'):
            host_list = [variables['ip']]
            transport = C.DEFAULT_TRANSPORT
        else:
            host_list = ['localhost']
            transport = 'local'

        play = PlayBook(
            playbook=action_file,
            remote_user=remote_user,
            host_list = host_list,
            private_key_file=private_key_file,
            extra_vars=variables,
            callbacks=playbook_cb,
            runner_callbacks=runner_cb,
            stats=stats,
            transport=transport)

        return play.run()
