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
import shutil
import tempfile

from jinja2 import Template

from solar.core.log import log
from solar.core.transports.ssh import SSHSyncTransport, SSHRunTransport


class BaseHandler(object):

    def __init__(self, resources, handlers=None):
        self.resources = resources
        if handlers is None:
            self.transport_sync = SSHSyncTransport()
            self.transport_run = SSHRunTransport()
        else:
            self.transport_run = handlers['run']()
            self.transport_sync = handlers['sync']()
        self.transport_sync.bind_with(self.transport_run)
        self.transport_run.bind_with(self.transport_sync)

    def __enter__(self):
        return self

    def __exit__(self, exc, value, traceback):
        return


class TempFileHandler(BaseHandler):
    def __init__(self, resources, handlers=None):
        super(TempFileHandler, self).__init__(resources, handlers)
        self.dst = tempfile.mkdtemp()

    def __enter__(self):
        self.dirs = {}
        for resource in self.resources:
            resource_dir = tempfile.mkdtemp(suffix=resource.name, dir=self.dst)
            self.dirs[resource.name] = resource_dir
        return self

    def __exit__(self, type, value, traceback):
        log.debug(self.dst)
        return
        shutil.rmtree(self.dst)

    def _compile_action_file(self, resource, action):
        dir_path = self.dirs[resource.name]
        dest_file = tempfile.mkstemp(text=True, prefix=action, dir=dir_path)[1]

        with open(dest_file, 'w') as f:
            f.write(self._render_action(resource, action))

        return dest_file

    def _render_action(self, resource, action):
        log.debug('Rendering %s %s', resource.name, action)

        action_file = resource.metadata['actions'][action]
        action_file = os.path.join(resource.metadata['actions_path'], action_file)
        log.debug('action file: %s', action_file)
        args = self._make_args(resource)

        with open(action_file) as f:
            tpl = Template(f.read())
        return tpl.render(str=str, zip=zip, **args)

    def _copy_templates_and_scripts(self, resource, action):
        # TODO: we might need to optimize it later, like provide list
        # templates/scripts per action
        log.debug("Adding templates for %s %s", resource.name, action)
        trg_templates_dir = None
        trg_scripts_dir = None

        base_path = resource.metadata['base_path']
        src_templates_dir = os.path.join(base_path, 'templates')
        if os.path.exists(src_templates_dir):
            trg_templates_dir = os.path.join(self.dirs[resource.name], 'templates')
            shutil.copytree(src_templates_dir, trg_templates_dir)

        src_scripts_dir = os.path.join(base_path, 'scripts')
        if os.path.exists(src_scripts_dir):
            trg_scripts_dir = os.path.join(self.dirs[resource.name], 'scripts')
            shutil.copytree(src_scripts_dir, trg_scripts_dir)

        return (trg_templates_dir, trg_scripts_dir)

    def prepare_templates_and_scripts(self, resource, action, target_dir=None):
        target_dir = target_dir or self.dirs[resource.name]
        templates, scripts = self._copy_templates_and_scripts(resource, action)
        if templates:
            self.transport_sync.copy(resource, templates, target_dir)
        if scripts:
            self.transport_sync.copy(resource, scripts, target_dir)

    def _make_args(self, resource):
        args = {'resource_name': resource.name}
        args['resource_dir'] = resource.metadata['base_path']
        args['templates_dir'] = 'templates/'
        args['scripts_dir'] = 'scripts/'
        args.update(resource.args)
        return args


class Empty(BaseHandler):
    def action(self, resource, action):
        pass
