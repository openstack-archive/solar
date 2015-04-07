import io
import os

import yaml

from solar.extensions import base


class Discovery(base.BaseExtension):

    VERSION = '1.0.0'
    ID = 'discovery'
    PROVIDES = ['nodes_resources']

    FILE_PATH = os.path.join(
        # TODO(pkaminski): no way we need '..' here...
        os.path.dirname(__file__), '..', '..', '..', '..',
        'examples', 'nodes_list.yaml')

    def execute(self):
        with io.open(self.FILE_PATH) as f:
            nodes = yaml.load(f)

        for node in nodes:
            node['tags'] = []

        self.db['node_list'] = yaml.dump(nodes, default_flow_style=False)

        return nodes

    def nodes_resources(self):
        nodes_list = self.db.get_copy('node_list')
        nodes_resources = []

        for node in nodes_list:
            node_resource = {}
            node_resource['id'] = node['id']
            node_resource['name'] = node['id']
            node_resource['handler'] = 'data'
            node_resource['type'] = 'resource'
            node_resource['version'] = self.VERSION
            node_resource['tags'] = node['tags']
            node_resource['output'] = node
            node_resource['ssh_host'] = node['ip']
            # TODO replace it with ssh type
            node_resource['connection_type'] = 'local'

            nodes_resources.append(node_resource)

        return nodes_resources
