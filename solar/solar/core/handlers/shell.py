# -*- coding: utf-8 -*-
from fabric import api as fabric_api

from solar.core.handlers.base import BaseHandler


class Shell(BaseHandler):
    def action(self, resource, action_name):
        action_file = self._compile_action_file(resource, action_name)
        fabric_api.local('bash {}'.format(action_file))
