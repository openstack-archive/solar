# -*- coding: UTF-8 -*-
import subprocess

from x.handlers.base import BaseHandler


class Shell(BaseHandler):
    def action(self, resource, action_name):
        action_file = self._compile_action_file(resource, action_name)
        subprocess.call(['bash', action_file])
