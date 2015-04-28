# -*- coding: UTF-8 -*-
import os
import shutil
import tempfile

from jinja2 import Template


class BaseHandler(object):
    def __init__(self, resources):
        self.dst = tempfile.mkdtemp()
        self.resources = resources

    def __enter__(self):
        self.dirs = {}
        for resource in self.resources:
            resource_dir = tempfile.mkdtemp(suffix=resource.name, dir=self.dst)
            self.dirs[resource.name] = resource_dir
        return self

    def __exit__(self, type, value, traceback):
        print self.dst
        return
        shutil.rmtree(self.dst)

    def _compile_action_file(self, resource, action):
        action_file = resource.metadata['actions'][action]
        action_file = os.path.join(resource.base_dir, 'actions', action_file)
        dir_path = self.dirs[resource.name]
        dest_file = tempfile.mkstemp(text=True, prefix=action, dir=dir_path)[1]
        args = self._make_args(resource)
        self._compile_file(action_file, dest_file, args)
        return dest_file

    def _compile_file(self, template, dest_file, args):
        with open(template) as f:
            tpl = Template(f.read())
            tpl = tpl.render(args)

            with open(dest_file, 'w') as g:
                g.write(tpl)

    def _make_args(self, resource):
        args = {'name' : resource.name}
        args['resource_dir'] = resource.base_dir
        args.update(resource.args)
        return args


class Empty(BaseHandler):
    def action(self, resource, action):
        pass
