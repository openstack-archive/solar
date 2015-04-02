
class BaseResource(object):

    def __init__(self, config):
        """
        config - data described in configuration files
        hosts  - can be overwritten if resource is inside of the role,
                 or maybe change for some resource directly
        """
        self.config = config
        self.uid = config['id']

    def prepare(self):
        """Make some changes in database state."""

    @property
    def inventory(self):
        """Return data that will be used for inventory"""
        return {self.uid: self.config.get('input', {})}

    def execute(self, action):
        """Return data that will be used by orchestration framework"""
        raise NotImplemented('Mandatory to overwrite')
