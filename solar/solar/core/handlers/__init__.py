# -*- coding: utf-8 -*-
from solar.core.handlers.ansible import Ansible
from solar.core.handlers.base import Empty
from solar.core.handlers.puppet import Puppet
from solar.core.handlers.shell import Shell
from solar.core.handlers.local_ansible import LocalAnsible


HANDLERS = {'ansible': Ansible,
            'puppet': Puppet,
            'shell': Shell,
            'none': Empty,
            'local_ansible': LocalAnsible}

def get(handler_name):
    handler = HANDLERS.get(handler_name, None)
    if handler:
        return handler
    raise Exception('Handler {0} does not exist'.format(handler_name))
