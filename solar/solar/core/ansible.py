
import yaml

from solar.extensions import resource

from jinja2 import Template


ANSIBLE_INVENTORY = """
{% for node in nodes %}
{{node.node.name}} ansible_ssh_host={{node.node.ssh_host}} ansible_ssh_port={{node.node.ssh_port}}

{% endfor %}

{% for res in resources %}
[{{ res.uid }}]
{% for node in nodes %} {{node.node.name}} {% endfor %} {% endfor %}
"""


class AnsibleOrchestration(object):

    def __init__(self, resources):
        self.resources = [resource(r) for r in resources
                          if r['id'] != 'node']
        self.nodes = [resource(r) for r in resources
                      if r['id'] == 'node']

    @property
    def inventory(self):
        temp = Template(ANSIBLE_INVENTORY)
        node_data = [n.inventory for n in self.nodes]
        return temp.render(nodes=node_data, resources=self.resources)

    @property
    def vars(self):
        result = {}

        for res in self.resources:

            compiled = Template(yaml.dump(res.inventory))
            compiled = yaml.load(compiled.render(**result))

            result.update(compiled)

        return result

    def run(self, action='run'):
        all_playbooks = []

        for res in self.resources:

            all_playbooks.extend(res.execute(action))

        return all_playbooks

    def remove(self):
        return list(reversed(self.run(action='remove')))
