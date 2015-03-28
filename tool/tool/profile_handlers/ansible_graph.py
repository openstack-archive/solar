
"""The point of different ansible graph handlers is that graph data model
allows to decidy which tasks to run in background.
"""


import networkx as nx


class ProfileGraph(nx.DiGraph):

    def __init__(self, profile):
        super(ProfileGraph, self).__init__()

    def add_resources(self, entity):
        resources = entity.get('resources', [])
        for res in resources:
            self.add_resource(res)

    def add_resource(self, resource):
        self.add_node(resource['id'])
        for dep in resource.get('requires', []):
            self.add_edge(dep, resource['id'])
        for dep in resource.get('required_for', []):
            self.add_edge(resource['id'], dep)


def process(profile, resources):
    # here we should know how to traverse profile data model
    # that is specific to ansible

    graph = nx.DiGraph(profile)
