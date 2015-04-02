import io
import os

import yaml

from solar import utils
from solar.extensions import base


class Discovery(base.BaseResource):

    FILE_PATH = os.path.join(
        os.path.dirname(__file__), '..', '..', '..',
        'examples', 'nodes_list.yaml')

    def execute(self, db):
        with io.open(self.FILE_PATH) as f:
            nodes = yaml.load(f)

        for node in nodes:
            node['tags'] = []

        db['node_list'] = yaml.dump(nodes, default_flow_style=False)

        return nodes
