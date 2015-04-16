import os

from solar.extensions import base
from solar import utils


class Resources(base.BaseExtension):

    VERSION = '1.0.0'
    ID = 'resources'
    PROVIDES = ['resources']

    # Rewrite it to use golden resources from
    # the storage
    FILE_MASK = os.path.join(
        utils.read_config()['examples-dir'],
        'resources', '*.yml')

    def resources(self):
        resources = []
        for file_path in utils.find_by_mask(self.FILE_MASK):
            res = utils.yaml_load(file_path)
            res['parent_path'] = file_path
            resources.append(res)
        return resources
