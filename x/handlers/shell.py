# -*- coding: UTF-8 -*-
import subprocess

from x.handlers.base import BaseHandler


class Shell(BaseHandler):
    def action(self, resource, action):
        action_file = self._compile_action_file(resource, action)
        subprocess.call(['bash', action_file])
