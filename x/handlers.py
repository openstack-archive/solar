# -*- coding: UTF-8 -*-
import os
import subprocess
import tempfile

from jinja2 import Template


def get(handler_name):
    handler = HANDLERS.get(handler_name, None)
    if handler:
        return handler
    raise Exception('Handler {0} does not exist'.format(handler_name))


class Ansible(object):
    """TODO"""
    def __init__(self):
        pass

    def action(self, resource, action):
        pass

    def _get_connection(self, resource):
        return {'ssh_user': '',
                'ssh_key': '',
                'host': ''}

    def _create_inventory(self, dest_dir):
        pass

    def _create_playbook(self, dest_dir):
        pass


class Shell(object):
    def __init__(self):
        pass

    def action(self, resource, action):
        action_file = resource.metadata['actions'][action]
        action_file = os.path.join(resource.base_dir, action_file)
        with open(action_file) as f:
            tpl = Template(f.read())
            tpl = tpl.render(resource.args)

            tmp_file = tempfile.mkstemp(text=True)[1]
            with open(tmp_file, 'w') as f:
                f.write(tpl)

            subprocess.call(['bash', tmp_file])


class Empty(object):
    def action(self, resource, action):
        pass


HANDLERS = {'ansible': Ansible,
            'shell': Shell,
            'none': Empty}

