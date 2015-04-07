import os

import subprocess
import yaml

from solar import utils
from solar.extensions import base

from jinja2 import Template


ANSIBLE_INVENTORY = """
{% for node in nodes %}
{{node['name']}} ansible_ssh_host={{node['ssh_host']}} ansible_connection={{node['connection_type']}}
{% endfor %}

{% for res in resources %}
 [{{ res.id }}]
 {% for node in nodes_mapping[res.id] %}
  {{node['name']}}
 {% endfor %}
{% endfor %}
"""


def playbook(resource_path, playbook_name):
    resource_dir = os.path.dirname(resource_path)
    return {'include': '{0}'.format(
        os.path.join(resource_dir,  playbook_name))}


class AnsibleOrchestration(base.BaseExtension):

    ID = 'ansible'
    VERSION = '1.0.0'
    PROVIDES = ['configure']

    def __init__(self, *args, **kwargs):
        super(AnsibleOrchestration, self).__init__(*args, **kwargs)

        self.nodes = self._get_nodes()
        self.resources = self._get_resources_for_nodes(self.nodes)

    def _get_nodes(self):
        nodes = []
        for node in self.core.get_data('nodes_resources'):
            if self.profile.tags <= set(node.get('tags', [])):
                nodes.append(node)

        return nodes

    def _get_resources_for_nodes(self, nodes):
        """Retrieves resources which required for nodes deployment"""
        resources = []

        for node in nodes:
            node_tags = set(node.get('tags', []))
            result_resources = self._get_resources_with_tags(node_tags)
            resources.extend(result_resources)

        return dict((r['id'], r) for r in resources).values()

    def _get_resources_with_tags(self, tags):
        resources = []
        for resource in self.core.get_data('resources'):
            resource_tags = set(resource.get('tags', []))
            # If resource without tags, it means that it should
            # not be assigned to any node
            if not resource_tags:
                continue
            if resource_tags <= tags:
                resources.append(resource)

        return resources

    @property
    def inventory(self):
        temp = Template(ANSIBLE_INVENTORY)
        return temp.render(
            nodes_mapping=self._make_nodes_services_mapping(),
            resources=self.resources,
            nodes=self.nodes)

    def _make_nodes_services_mapping(self):
        mapping = {}
        for resource in self.resources:
            mapping[resource['id']] = self._get_nodes_for_resource(resource)

        return mapping

    def _get_nodes_for_resource(self, resource):
        resource_tags = set(resource['tags'])
        nodes = []
        for node in self.nodes:
            if resource_tags <= set(node['tags']):
                nodes.append(node)

        return nodes

    @property
    def vars(self):
        result = {}

        for res in self.resources:
            compiled = Template(
                utils.yaml_dump({res['id']: res.get('input', {})}))
            compiled = yaml.load(compiled.render(**result))

            result.update(compiled)

        return result

    def prepare_from_profile(self, profile_action):
        if profile_action not in self.profile:
            raise Exception('Action %s not supported', profile_action)

        paths = self.profile[profile_action]
        return self.execute_many(paths)

    def prepare_many(self, paths):

        ansible_actions = []

        for path in paths:
            ansible_actions.extend(self.prepare_one(path))

        return ansible_actions

    def prepare_one(self, path):
        """
        :param path: docker.actions.run or openstack.action
        """
        steps = path.split('.')

        if len(steps) < 2:
            raise Exception('Path %s is not valid,'
                            ' should be atleast 2 items', path)

        resource = next(res for res in self.resources
                        if res['id'] == steps[0])

        action = resource
        for step in steps[1:]:
            action = action[step]

        result = []
        if isinstance(action, list):
            for item in action:
                result.append(playbook(resource['parent_path'], item))
        else:
            result.append(playbook(resource['parent_path'], action))

        return result

    def configure(self, profile_action='run', actions=None):
        utils.create_dir('tmp/group_vars')
        utils.write_to_file(self.inventory, 'tmp/hosts')
        utils.yaml_dump_to(self.vars, 'tmp/group_vars/all')

        if actions:
            prepared = self.prepare_many(actions)
        elif profile_action:
            prepared = self.prepare_from_profile(profile_action)
        else:
            raise Exception('Either profile_action '
                            'or actions should be provided.')

        utils.yaml_dump_to(prepared, 'tmp/main.yml')

        sub = subprocess.Popen(
            ['ansible-playbook', '-i', 'tmp/hosts', 'tmp/main.yml'])
        out, err = sub.communicate()
