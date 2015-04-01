
from solar.extensions import base


class Playbook(base.BaseResource):

    def execute(self, action):
        return self.config.get('actions', {}).get(action, [])
