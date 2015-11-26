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
import errno

from solar import utils
from solar.core.log import log
from solar.core.transports.ssh import SSHSyncTransport, SSHRunTransport


tempfile.gettempdir()

SOLAR_TEMP_LOCAL_LOCATION = os.path.join(tempfile.tempdir, 'solar_local')


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
        self.dst = None

    def __enter__(self):
        try:
            self.dst = tempfile.mkdtemp(dir=SOLAR_TEMP_LOCAL_LOCATION)
        except OSError as ex:
            if ex.errno == errno.ENOENT:
                os.makedirs(SOLAR_TEMP_LOCAL_LOCATION)
                self.dst = tempfile.mkdtemp(dir=SOLAR_TEMP_LOCAL_LOCATION)
            else:
                raise
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

        action_file = resource.actions[action]
        log.debug('action file: %s', action_file)
        args = self._make_args(resource)

        return utils.render_template(
            action_file,
            str=str,
            zip=zip,
            **args)

    def _render_dir(self, resource, _path):
        args = self._make_args(resource)
        for f in os.listdir(_path):
            if f.endswith('.jinja'):
                target_f = f[:-6]
                full_target = os.path.join(_path, target_f)
                full_src = os.path.join(_path, f)
                with open(full_target, 'wb') as tmpl_f:
                    tpl = utils.render_template(
                        full_src,
                        str=str,
                        zip=zip,
                        **args)
                    tmpl_f.write(tpl)
                log.debug("Rendered: %s", full_target)
                os.remove(full_src)

    def _copy_templates_and_scripts(self, resource, action):
        # TODO: we might need to optimize it later, like provide list
        # templates/scripts per action
        log.debug("Adding templates for %s %s", resource.name, action)
        trg_templates_dir = None
        trg_scripts_dir = None

        base_path = resource.db_obj.base_path
        src_templates_dir = os.path.join(base_path, 'templates')
        if os.path.exists(src_templates_dir):
            trg_templates_dir = os.path.join(
                self.dirs[resource.name], 'templates')
            shutil.copytree(src_templates_dir, trg_templates_dir)

        src_scripts_dir = os.path.join(base_path, 'scripts')
        if os.path.exists(src_scripts_dir):
            trg_scripts_dir = os.path.join(self.dirs[resource.name], 'scripts')
            shutil.copytree(src_scripts_dir, trg_scripts_dir)

        if trg_templates_dir:
            self._render_dir(resource, trg_templates_dir)

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
        args['resource_dir'] = resource.db_obj.base_path
        args['templates_dir'] = 'templates/'
        args['scripts_dir'] = 'scripts/'
        args.update(resource.args)
        return args


class Empty(BaseHandler):

    def action(self, resource, action):
        pass
