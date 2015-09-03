# -*- coding: utf-8 -*-
from fabric import api as fabric_api
from fabric.state import env
import os

from solar.core.log import log
from solar.core.handlers.base import TempFileHandler
from solar import errors


# otherwise fabric will sys.exit(1) in case of errors
env.warn_only = True

class AnsibleTemplate(TempFileHandler):
    def action(self, resource, action_name):
        inventory_file = self._create_inventory(resource)
        playbook_file = self._create_playbook(resource, action_name)
        log.debug('inventory_file: %s', inventory_file)
        log.debug('playbook_file: %s', playbook_file)
        call_args = ['ansible-playbook', '--module-path', '/vagrant/library', '-i', inventory_file, playbook_file]
        log.debug('EXECUTING: %s', ' '.join(call_args))

        with fabric_api.shell_env(ANSIBLE_HOST_KEY_CHECKING='False'):
            out = fabric_api.local(' '.join(call_args), capture=True)
        if out.failed:
            raise errors.SolarError(out)


    def _create_inventory(self, r):
        directory = self.dirs[r.name]
        inventory_path = os.path.join(directory, 'inventory')
        with open(inventory_path, 'w') as inv:
            inv.write(self._render_inventory(r))
        return inventory_path

    def _render_inventory(self, r):
        inventory = '{0} ansible_ssh_host={1} ansible_connection=ssh ansible_ssh_user={2} ansible_ssh_private_key_file={3} {4}'
        host, user, ssh_key = r.args['ip'].value, r.args['ssh_user'].value, r.args['ssh_key'].value
        args = []
        for arg in r.args:
            args.append('{0}="{1}"'.format(arg, r.args[arg].value))
        args = ' '.join(args)
        inventory = inventory.format(host, host, user, ssh_key, args)
        log.debug(inventory)
        return inventory

    def _create_playbook(self, resource, action):
        return self._compile_action_file(resource, action)
