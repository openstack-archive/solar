

import os
from fnmatch import fnmatch

import yaml


def get_files(path, pattern):
    for root, dirs, files in os.walk(path):
        for file_name in files:
            if fnmatch(file_name, file_pattern):
                yield os.path.join(root, file_name)


class Storage(object):

    def __init__(self):
        self.entities = {}

    def add(self, resource):
        if 'id' in resource:
            self.entities[resource['id']] = resource

    def add_profile(self, profile):
        self.entities[profile['id']] = profile
        for res in profile.get('resources', []):
            self.add_resource(res)

    def add_resource(self, resource):
        if 'id' in resource:
            self.entities[resource['id']] = resource

    def add_service(self, service):
        if 'id' in service:
            self.entities[service['id']] = service
            for resource in service.get('resources', []):
                self.add_resource(resource)

    def get(self, resource_id):
        return self.entities[resource_id]

    @classmethod
    def from_files(self, path):
        for file_path in get_files(path, '*.yml'):
            with open(file_path) as f:
                entity = yaml.load(f)

            if entity['type'] == 'profile':
                self.add_profile(entity)
            elif entity['type'] == 'resource':
                self.add_resource(entity)
            elif entity['type'] == 'service':
                self.add_service(entity)
