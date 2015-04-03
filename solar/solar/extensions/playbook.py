
from solar.extensions import base


class Playbook(base.BaseExtension):

    NAME = 'ansible_playbook'
    VERSION = '1.0.0'

    def execute(self, action):
        return self.config.get('actions', {}).get(action, [])
