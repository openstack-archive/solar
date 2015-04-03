from solar.interfaces.db import get_db


class BaseExtension(object):

    ID = None
    NAME = None

    def __init__(self, config):
        self.config = config
        self.uid = self.ID
        self.db = get_db()

    def prepare(self):
        """Make some changes in database state."""

    @property
    def inventory(self):
        """Return data that will be used for inventory"""
        return {self.uid: self.input}

    @property
    def input(self):
        return self.config.get('input', {})

    def execute(self, action):
        """Return data that will be used by orchestration framework"""
        raise NotImplemented('Mandatory to overwrite')
