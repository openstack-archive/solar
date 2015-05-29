
def depends_on(init_value, value=None, tags=None):
    if tags is None:
        tags = []

    if value is None:
        value = init_value

    called_with_tags = []

    if isinstance(value, dict):
        if value.get('first_resource'):
            called_with_tags.extend(value.get('first_resource'))
        elif value.get('filter_resources'):
            called_with_tags.extend(value.get('filter_resources'))

        for k, v in value.items():
            depends_on(init_value, value=v, tags=tags)
    elif isinstance(value, list):
        for e in value:
            depends_on(init_value, value=e, tags=tags)
    elif isinstance(value, str):
        return value

    tags.extend(called_with_tags)

    return tags


class ResourcesConnectionGraph(object):

    def __init__(self, connections, resources, *args, **kwargs):
        super(ResourcesConnectionGraph, self).__init__(*args, **kwargs)
        self.connections = connections
        self.resources = resources

    def iter_connections(self):
        for connection in self.connections:
            connections_from = self.resources_with_tags(depends_on(connection))
            connections_to = self.resources_with_tags(connection['for_resources'])
            mapping = self.make_mapping(connection)

            for connection_from in connections_from:
                for connection_to in connections_to:
                    if connection_from == connection_to:
                        continue

                    yield {'from': connection_from, 'to': connection_to, 'mapping': mapping}

    def resources_with_tags(self, tags):
        """Filter all resources which have tags
        """
        return filter(lambda r: set(r.tags) & set(tags), self.resources)

    def make_mapping(self, connection):
        return connection['mapping']
