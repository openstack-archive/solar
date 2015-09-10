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

from solar.core.handlers.ansible_template import AnsibleTemplate
from solar.core.handlers.ansible_playbook import AnsiblePlaybook
from solar.core.handlers.base import Empty
from solar.core.handlers.puppet import Puppet
from solar.core.handlers.shell import Shell


HANDLERS = {'ansible': AnsibleTemplate,
            'ansible_playbook': AnsiblePlaybook,
            'shell': Shell,
            'puppet': Puppet,
            'none': Empty}

def get(handler_name):
    handler = HANDLERS.get(handler_name, None)
    if handler:
        return handler
    raise Exception('Handler {0} does not exist'.format(handler_name))
