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
{% for node in nodes %} {{node['name']}} {% endfor %} {% endfor %}
"""


class AnsibleOrchestration(base.BaseExtension):

    ID = 'ansible'
    VERSION = '1.0.0'
    PROVIDES = ['configure']

    def __init__(self, *args, **kwargs):
        super(AnsibleOrchestration, self).__init__(*args, **kwargs)

        self.resources = self.core.get_data('resources')
        self.nodes = self._get_nodes()

    def _get_nodes(self):
        nodes = []
        for node in self.core.get_data('nodes_resources'):
            if self.profile.tags <= set(node.get('tags', [])):
                nodes.append(node)

        return nodes

    def _get_resources_for_nodes(self):
        pass

    @property
    def inventory(self):
        temp = Template(ANSIBLE_INVENTORY)
        return temp.render(nodes=self.nodes, resources=self.resources)

    @property
    def vars(self):
        result = {}

        for res in self.resources:
            compiled = Template(utils.yaml_dump({res['id']: res.get('input', {})}))
            compiled = yaml.load(compiled.render(**result))

            result.update(compiled)

        return result

    def run(self, action='run'):
        all_playbooks = []

        for res in self.resources:
            all_playbooks.extend(res.get('actions', {}).get(action, {}))

        return all_playbooks

    def remove(self):
        return list(reversed(self.run(action='remove')))

    def configure(self):
        utils.create_dir('tmp/group_vars')
        utils.write_to_file(self.inventory, 'tmp/hosts')
        utils.yaml_dump_to(self.vars, 'tmp/group_vars/all')
        utils.yaml_dump_to(self.run(), 'tmp/main.yml')

        sub = subprocess.Popen(
            ['ansible-playbook', '-i', 'tmp/hosts', 'tmp/main.yml'])
        out, err = sub.communicate()
