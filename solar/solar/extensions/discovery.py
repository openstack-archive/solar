import io
import os

import yaml

from solar import utils
from solar.extensions import base


class Discovery(base.BaseResource):

    VERSION = '1.0.0'

    FILE_PATH = os.path.join(
        os.path.dirname(__file__), '..', '..', '..',
        'examples', 'nodes_list.yaml')

    def execute(self):
        with io.open(self.FILE_PATH) as f:
            nodes = yaml.load(f)

        for node in nodes:
            node['tags'] = []

        self.db['node_list'] = yaml.dump(nodes, default_flow_style=False)

        return nodes

    def resources(self):
        nodes_list = self.db.get_copy('node_list')
        nodes_resources = []

        for node in nodes_list:
            node_resource = {}
            node_resource['id'] = node['id']
            node_resource['handler'] = 'data'
            node_resource['type'] = 'resource'
            node_resource['version'] = self.VERSION
            node_resource['output'] = node
            node_resource['required_for'] = node['tags']

            nodes_resources.append(node_resource)

        return nodes_resources
