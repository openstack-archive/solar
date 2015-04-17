
import copy
from pprint import pprint

import networkx as nx


class Resource(object):

    def __init__(self, config):
        self.uid = config['id']
        self.values = config['input']
        self.tags = set(config.get('tags', ()))

    def __repr__(self):
        return 'Resource(uid={0},tags={1})'.format(self.uid, self.tags)

    def __hash__(self):
        return hash(self.uid)

    @property
    def links(self):
        for item, value in self.values.items():
            if 'link' in value:
                yield value['link'], {'parent': item}


class DataGraph(nx.DiGraph):

    node_klass = Resource

    def __init__(self, resources=(), *args, **kwargs):
        super(DataGraph, self).__init__(*args, **kwargs)

        for res in resources:
            init_res = self.node_klass(res)
            self.add_node(init_res.uid, res=init_res)

            for link, attrs in init_res.links:
                self.add_edge(init_res.uid, link, **attrs)

    def resolve(self):
        data = {}

        for item in nx.topological_sort(self.reverse()):
            res = self.node[item]['res']
            res_data = copy.deepcopy(res.values)
            res_data['tags'] = res.tags

            for child, parent, attrs in self.edges(item, data=True):
                res_data[attrs['parent']] = data[parent]
            data[item] = res_data

        return data
