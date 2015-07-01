# -*- coding: utf-8 -*-
from solar.core.handlers.ansible_template import AnsibleTemplate
from solar.core.handlers.ansible_playbook import AnsiblePlaybook
from solar.core.handlers.base import Empty
from solar.core.handlers.puppet import Puppet
from solar.core.handlers.shell import Shell


HANDLERS = {'ansible': AnsibleTemplate,
            'ansible_playbook': AnsiblePlaybook,
            'shell': Shell,
            'none': Empty}

def get(handler_name):
    handler = HANDLERS.get(handler_name, None)
    if handler:
        return handler
    raise Exception('Handler {0} does not exist'.format(handler_name))
