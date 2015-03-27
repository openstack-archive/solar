
from tool.resource_handlers import playbook
from tool.service_handlers import base


class AnsibleProfile(object):
    """This profile should just serialize
    """

    def __init__(self, storage, config):
        self.config = config

    def inventory(self):
        pass


