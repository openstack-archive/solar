# -*- coding: utf-8 -*-
from fabric import api as fabric_api
from fabric.state import env
import os

from solar.core.log import log
from solar.core.handlers.base import TempFileHandler
from solar import errors


# otherwise fabric will sys.exit(1) in case of errors
env.warn_only = True

# if we would have something like solard that would render this then
# we would not need to render it there
# for now we redender it locally, sync to remote, run ansible on remote host as local
class AnsibleTemplate(TempFileHandler):
    def action(self, resource, action_name):
        inventory_file = self._create_inventory(resource)
        playbook_file = self._create_playbook(resource, action_name)
        log.debug('inventory_file: %s', inventory_file)
        log.debug('playbook_file: %s', playbook_file)

        # self.transport_sync.copy(resource, self.dirs[resource.name], self.dirs[resource.name])
        self.transport_sync.copy(resource, self.dst, '/tmp')
        self.transport_sync.copy(resource, '/vagrant/library', '/tmp')
        self.transport_sync.sync_all()

        call_args = ['ansible-playbook', '--module-path', '/tmp/library', '-i', inventory_file, playbook_file]
        log.debug('EXECUTING: %s', ' '.join(call_args))

        out = self.transport_run.run(resource, *call_args)
        log.debug(out)
        if out.failed:
            raise errors.SolarError(out)

        # with fabric_api.shell_env(ANSIBLE_HOST_KEY_CHECKING='False'):
        #     out = fabric_api.local(' '.join(call_args), capture=True)
        # if out.failed:
        #     raise errors.SolarError(out)


    def _create_inventory(self, r):
        directory = self.dirs[r.name]
        inventory_path = os.path.join(directory, 'inventory')
        with open(inventory_path, 'w') as inv:
            inv.write(self._render_inventory(r))
        return inventory_path

    def _render_inventory(self, r):
        # inventory = '{0} ansible_ssh_host={1} ansible_connection=ssh ansible_ssh_user={2} ansible_ssh_private_key_file={3} {4}'
        # host, user, ssh_key = r.args['ip'].value, r.args['ssh_user'].value, r.args['ssh_key'].value

        # XXX: r.args['ssh_user'] should be something different in this case probably
        inventory = '{0} ansible_connection=local user={1} {2}'
        host, user = 'localhost', r.args['ssh_user'].value
        args = []
        for arg in r.args:
            args.append('{0}="{1}"'.format(arg, r.args[arg].value))
        args = ' '.join(args)
        inventory = inventory.format(host, user, args)
        log.debug(inventory)
        return inventory

    def _create_playbook(self, resource, action):
        return self._compile_action_file(resource, action)

    def _make_args(self, resource):
        args = super(AnsibleTemplate, self)._make_args(resource)
        args['host'] = 'localhost'
        return args

