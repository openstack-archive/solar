
import copy
import json

from itertools import imap, ifilter
from pprint import pprint

import networkx as nx
import jinja2
import mock

from jinja2 import Template


class Node(object):

    def __init__(self, config):
        self.uid = config['id']
        self.tags = set(config.get('tags', ()))
        self.config = copy.deepcopy(config)

    def __repr__(self):
        return 'Node(uid={0},tags={1})'.format(self.uid, self.tags)


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
            if value.get('first_with_tags'):
                called_with_tags.extend(value.get('first_with_tags'))
            elif value.get('with_tags'):
                called_with_tags.extend(value.get('with_tags'))

            for k, v in value.items():
                self.depends_on(value=v, tags=tags)
        elif isinstance(value, list):
            for e in value:
                self.depends_on(value=e, tags=tags)
        elif isinstance(value, str):
            return value

        tags.extend(called_with_tags)

        return tags


class DataGraph(nx.DiGraph):

    node_klass = Resource

    def __init__(self, resources=(), nodes=(), *args, **kwargs):
        super(DataGraph, self).__init__(*args, **kwargs)
        self.resources = map(lambda r: self.node_klass(r), resources)
        self.nodes = map(lambda n: Node(n), nodes)
        self.init_edges()

    def init_edges(self):
        for res in self.resources:
            self.add_node(res.uid, res=res)

            for dep_res in self.resources_with_tags(res.depends_on()):
                self.add_node(dep_res.uid, res=dep_res)
                self.add_edge(res.uid, dep_res.uid, parent=res.uid)

    def resources_with_tags(self, tags):
        """Filter all resources which have tags
        """
        return ifilter(lambda r: r.tags & set(tags), self.resources)

    def merge_nodes_resources(self):
        """Each node has a list of resources
        """
        merged = {}
        for node in self.nodes:
            merged.setdefault(node.uid, {})
            merged[node.uid]['resources'] = list(self.resources_with_tags(node.tags))
            merged[node.uid]['node'] = node

        return merged

    def get_node(self, uid):
        return filter(lambda n: n.uid == uid, self.nodes)[0]

    def resolve(self):
        rendered_accum = {}
        render_order = nx.topological_sort(self.reverse())

        # Use provided order to render resources
        for resource_id in render_order:
            # Iterate over all resources which are assigned for node
            for node_id, node_data in self.merge_nodes_resources().items():
                # Render resources which should be rendered regarding to order
                for resource in filter(lambda r: r.uid == resource_id, node_data['resources']):
                    # Create render context
                    ctx = {
                        'this': resource.values,
                    }
                    ctx['this']['node'] = self.get_node(node_id).config

                    rendered = self.render(resource.values, ctx, rendered_accum)

                    rendered['tags'] = resource.tags
                    rendered_accum['{0}-{1}'.format(node_id, resource.uid)] = rendered

        return rendered_accum

    def render(self, value, context, previous_render):

        if isinstance(value, dict):
            # Handle iterators
            if value.get('first_with_tags') or value.get('with_tags'):

                if len(value.keys()) != 2:
                    raise Exception("Iterator should have two elements '{0}'".format(value))

                def with_tags(*args):
                    resources_with_tags = filter(
                        lambda n: n[1]['tags'] & set(list(*args)),
                        previous_render.items())

                    return map(lambda n: n[1], resources_with_tags)

                method_name = 'with_tags'
                if value.get('first_with_tags'):
                    method_name = 'first_with_tags'

                iter_key = (set(value.keys()) - set([method_name])).pop()

                items = []
                if isinstance(value[method_name], list):
                    items = with_tags(value[method_name])
                elif isinstance(value[method_name], str):
                    items = with_tags([value[method_name]])
                else:
                    raise Exception('Cannot iterate over dict "{0}"'.format(value))

                # first_with_tags returns a single object, hence we should
                # render a single object
                if value.get('first_with_tags'):
                    if len(items) > 1:
                        raise Exception('Returns too many objects, check that '
                                        'tags assigned properly "{0}"'.format(value))

                    iter_ctx = copy.deepcopy(context)
                    iter_ctx[iter_key] = items[0]
                    return self.render(value[iter_key], iter_ctx, previous_render)

                # If it's with_tags construction, than it returns a list
                # we should render each element and return a list of rendered
                # elements
                result_list = []
                for item in items:
                    iter_ctx = copy.deepcopy(context)
                    iter_ctx[iter_key] = item
                    result_list.append(self.render(value[iter_key], iter_ctx, previous_render))

                return result_list

            else:
                # Handle usual data
                result_dict = {}
                for k, v in value.items():
                    result_dict[k] = self.render(v, context, previous_render)

                return result_dict
        elif isinstance(value, list):
            return map(lambda v: self.render(v, context, previous_render), value)
        elif isinstance(value, str):
            env = Template(value)
            return env.render(**context)
        else:
            # If non of above return value, e.g. if there is
            # interger, float etc
            return value
