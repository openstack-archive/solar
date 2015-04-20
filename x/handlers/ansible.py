# -*- coding: UTF-8 -*-
import os
import subprocess

from x.handlers.base import BaseHandler


class Ansible(BaseHandler):
    def action(self, resource, action_name):
        inventory_file = self._create_inventory(resource)
        playbook_file = self._create_playbook(resource, action_name)
        subprocess.call(['ansible-playbook', '-i', inventory_file, playbook_file])

    #def _get_connection(self, resource):
    #    return {'ssh_user': '',
    #            'ssh_key': '',
    #            'host': ''}

    def _create_inventory(self, r):
        inventory = '{0} ansible_ssh_host={1} ansible_connection=ssh ansible_ssh_user={2} ansible_ssh_private_key_file={3}'
        host, user, ssh_key = r.args['ip'], r.args['ssh_user'], r.args['ssh_key']
        print host
        print user
        print ssh_key
        inventory = inventory.format(host, host, user, ssh_key)
        directory = self.dirs[r.name]
        inventory_path = os.path.join(directory, 'inventory')
        with open(inventory_path, 'w') as inv:
            inv.write(inventory)
        return inventory_path

    def _create_playbook(self, resource, action):
        return self._compile_action_file(resource, action)
