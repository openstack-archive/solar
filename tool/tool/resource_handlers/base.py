


class BaseResource(object):

    def __init__(self, config, hosts='all'):
        """
        config - data described in configuration files
        hosts  - can be overwritten if resource is inside of the role,
                 or maybe change for some resource directly
        """
        self.config = config
        self.uid = config['id']
        self.hosts = hosts

    def prepare(self):
        """Make some changes in database state."""

    def inventory(self):
        """Return data that will be used for inventory"""
        if 'parameters' in self.config:
            params = self.config.get('parameters', {})

        res = {}

        for param, values in self.config.parameters.items():
            res[param] = values.get('value') or values.get('default')

        return res


    def run(self):
        """Return data that will be used by orchestration framework"""
        raise NotImplemented('Mandatory to overwrite')
