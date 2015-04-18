
import copy

from pprint import pprint

import networkx as nx
import jinja2
import mock

from jinja2 import Template


class Resource(object):

    def __init__(self, config):
        self.uid = config['id']
        self.values = config['input']
        self.tags = set(config.get('tags', ()))

    def __repr__(self):
        return 'Resource(uid={0},tags={1})'.format(self.uid, self.tags)

    def __hash__(self):
        return hash(self.uid)

    def depends_on(self, value=None, tags=None):
        if tags is None:
            tags = []

        if value is None:
            value = self.values

        called_with_tags = []

        if isinstance(value, dict):
            for k, v in value.items():
                self.depends_on(value=v, tags=tags)
        elif isinstance(value, list):
            for e in value:
                self.depends_on(value=e, tags=tags)
        elif isinstance(value, str):
            env = Template(value)
            tags_call_mock = mock.MagicMock()

            env.globals['with_tags'] = tags_call_mock
            env.globals['first_with_tags'] = tags_call_mock

            try:
                env.render()
            except jinja2.exceptions.UndefinedError:
                # On dependency resolving stage we should
                # not handle rendering errors, we need
                # only information about graph, this
                # information can be provided by tags
                # filtering calls
                pass

            # Get arguments, which are tags, and flatten the list
            used_tags = sum(map(
                lambda call: list(call[0]),
                tags_call_mock.call_args_list), [])

            called_with_tags.extend(used_tags)

        tags.extend(called_with_tags)

        return tags


class DataGraph(nx.DiGraph):

    node_klass = Resource

    def __init__(self, resources=(), *args, **kwargs):
        super(DataGraph, self).__init__(*args, **kwargs)

        for res in resources:
            init_res = self.node_klass(res)
            self.add_node(init_res.uid, res=init_res)

            print init_res.depends_on()

            # for link, attrs in init_res.depends_on():
            #     self.add_edge(init_res.uid, link, **attrs)

    def resolve(self):
        return
        data = {}

        for item in nx.topological_sort(self.reverse()):
            res = self.node[item]['res']
            res_data = copy.deepcopy(res.values)
            res_data['tags'] = res.tags

            for child, parent, attrs in self.edges(item, data=True):
                res_data[attrs['parent']] = data[parent]
            data[item] = res_data

        return data
