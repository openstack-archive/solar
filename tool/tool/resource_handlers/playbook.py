"""
Just find or create existing playbook.
"""

from tool.resource_handlers import base


class Playbook(base.BaseResource):

    def run(self):
        return {
            'hosts': self.hosts,
            'tasks': self.config.get('run', []),
            'sudo': 'yes'}
