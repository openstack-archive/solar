import os

import subprocess
import yaml

from solar import utils
from solar.extensions import base
from solar.core import data

from jinja2 import Template


ANSIBLE_INVENTORY = """
{% for key, res in resources.items() %}
{% if res.node %}
{{key}} ansible_ssh_host={{res.node.ip}} ansible_connection=ssh ansible_ssh_user={{res.node.ssh_user}} ansible_ssh_private_key_file={{res.node.ssh_private_key_path}}
{% endif %}
{% endfor %}
{% for key, group in groups.items() %}
[{{key}}]
{% for item in group %}
{{item}}
{% endfor %}
{% endfor %}
"""

BASE_PATH=utils.read_config()['tmp']

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


    def inventory(self, **kwargs):
        temp = Template(ANSIBLE_INVENTORY)
        return temp.render(**kwargs)

    def _make_nodes_services_mapping(self):
        mapping = {}
        for resource in self.resources:
            mapping[resource['id']] = self._get_nodes_for_resource(resource)

        return mapping


    def prepare_from_profile(self, profile_action):

        paths = self.profile.get(profile_action)
        if paths is None:
            raise Exception('Action %s not supported', profile_action)

        return self.prepare_many(paths)

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

        resources = filter(lambda r: r['id'] == steps[0], self.resources)
        # NOTE: If there are not resouces for this tags, just skip it
        if not resources:
            return []

        resource = resources[0]

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
        dg = data.DataGraph(self.nodes + self.resources)
        resolved = dg.resolve()

        groups = {}

        for key, resource in resolved.items():
            if resource.get('node'):
                for tag in resource.get('tags', []):
                    groups.setdefault(tag, [])
                    groups[tag].append(key)

        utils.create_dir('tmp/group_vars')
        utils.create_dir('tmp/host_vars')
        utils.write_to_file(
            self.inventory(
                resources=resolved, groups=groups), 'tmp/hosts')


        for item, value in resolved.items():
            utils.yaml_dump_to(
                value, 'tmp/host_vars/{0}'.format(item))

        if actions:
            prepared = self.prepare_many(actions)
        elif profile_action:
            prepared = self.prepare_from_profile(profile_action)
        else:
            raise Exception('Either profile_action '
                            'or actions should be provided.')

        utils.yaml_dump_to(prepared, BASE_PATH + '/main.yml')

        sub = subprocess.Popen(
            ['ansible-playbook', '-i',
              BASE_PATH + '/hosts',
              BASE_PATH + '/main.yml'],
            env=dict(os.environ, ANSIBLE_HOST_KEY_CHECKING='False'))
        out, err = sub.communicate()
