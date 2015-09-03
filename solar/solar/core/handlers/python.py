# -*- coding: utf-8 -*-
from fabric import api as fabric_api

from solar.core.handlers.base import TempFileHandler


class Python(TempFileHandler):
    def action(self, resource, action_name):
        action_file = self._compile_action_file(resource, action_name)
        fabric_api.local('python {}'.format(action_file))
