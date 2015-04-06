import io
import os

import yaml

from solar import utils
from solar.extensions import base


class Resources(base.BaseExtension):

    VERSION = '1.0.0'
    ID = 'resources'
    PROVIDES = ['resources']

    # Rewrite it to use golden resources from
    # the storage
    FILE_MASK = os.path.join(
        os.path.dirname(__file__), '..', '..', '..',
        'schema', 'resources', '*.yml')

    def resources(self):
        return utils.load_by_mask(self.FILE_MASK)
