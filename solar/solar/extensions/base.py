from solar.interfaces.db import get_db


class BaseExtension(object):

    ID = None
    NAME = None
    PROVIDES = []

    def __init__(self, profile, core_manager=None, config=None):
        self.config = config or {}
        self.uid = self.ID
        self.db = get_db()
        self.profile = profile

        from solar.core.extensions_manager import ExtensionsManager
        self.core = core_manager or ExtensionsManager(self.profile)

    def prepare(self):
        """Make some changes in database state."""

    @property
    def input(self):
        return self.config.get('input', {})

    @property
    def output(self):
        return self.config.get('output', {})
