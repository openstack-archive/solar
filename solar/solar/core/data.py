
import copy
from pprint import pprint


class Data(object):

    def __init__(self, nodes, resources):
        self.resources = [Resource(r) for r in resources]
        self.nodes = [Node(n) for n in nodes]

        self.raw = {'hosts': []}

        for node in self.nodes:
            self.raw['hosts'].append(node.data)

            for res in self.resources:
                if not res.tags:
                    continue
                if res.tags <= node.tags:
                    node.data[res.uid] = res.data

    def get(self):
        # recursively go over variables
        for node in self.nodes:

            for res in self.resources:
                if not res.tags:
                    continue
                if res.tags <= node.tags:
                    for link in res.links:
                        link.resolve(node.data)
        return self.raw


class Link(object):
    """Represents reference to another resource."""

    def __init__(self, path, parent):
        self.parent = parent.split('.')
        self.path = path

    def resolve(self, glob_data):
        data = glob_data

        for item in self.parent:
            data = data[item]

        if isinstance(data, Link):
            value = data.resolve(glob_data)
        else:
            value = data

        self.set_value(glob_data, value)

    def set_value(self, glob_data, value):
        data = glob_data
        for item in self.path[:-1]:
            data = data[item]
        data[self.path[-1]] = value

    def __repr__(self):
        return 'Link(path={0},parent={1})'.format(
            self.path, self.parent)


class Node(object):

    def __init__(self, config):
        self.uid = config['id']
        self.config = config
        self.tags = set(config.get('tags', ()))
        self.data = copy.deepcopy(self.config)

    def __repr__(self):
        return 'Node(uid={0},tags={1})'.format(self.uid, self.tags)


class Resource(object):

    def __init__(self, config):
        self.uid = config['id']
        self.config = config
        self.tags = set(config.get('tags', ()))
        self.links = []

    @property
    def data(self):
        _data = {}
        for key, value in self.config.get('values', {}).items():
            path = [self.uid, key]
            if isinstance(value, dict):
                if 'link' in value:
                    link = Link(path, value['link'])
                    _data[key] = link
                    self.links.append(link)
            else:
                _data[key] = value
        return _data

    def __repr__(self):
        return 'Resource(uid={0},tags={1})'.format(self.uid, self.tags)


if __name__ == '__main__':

    nodes = [
        {'id': 'node_1', 'host_ip': '10.0.0.2', 'tags': ['service']},
        {'id': 'node_2', 'host_ip': '10.0.0.3', 'tags': ['service']}]
    resources = [
        {'id': 'service',
         'tags': ['service'],
         'values': {'listen': {'link':'host_ip'}}}]

    inv = Data(nodes, resources)
    pprint(inv.get())
