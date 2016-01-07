#!/usr/bin/env python

import click
import sys

from solar.core import resource
from solar.core import signals
from solar.core import validation
from solar.core.resource import composer as cr
from solar import events as evapi
from solar.dblayer.model import ModelMeta

PROFILE = False
#PROFILE = True


if PROFILE:
    import StringIO
    import cProfile
    import pstats

    pr = cProfile.Profile()
    pr.enable()


# TODO
# Resource for repository OR puppet apt-module in run.pp
# add-apt-repository cloud-archive:juno
# To discuss: install stuff in Docker container

# NOTE
# No copy of manifests, pull from upstream (implemented in the librarian resource)
# Official puppet manifests, not fuel-library



@click.group()
def main():
    pass


def prepare_nodes(nodes_count):
    resources = cr.create('nodes', 'templates/nodes', {"count": nodes_count})
    nodes = resources.like('node')
    resources = cr.create('nodes_network', 'templates/nodes_network', {"count": nodes_count})
    nodes_sdn = resources.like('node')
    r = {}

    for node, node_sdn in zip(nodes, nodes_sdn):
        r[node.name] = node
        r[node_sdn.name] = node_sdn

        # LIBRARIAN
        librarian = cr.create('librarian_{}'.format(node.name), 'resources/librarian', {})[0]
        r[librarian.name] = librarian

        node.connect(librarian, {})

        # NETWORKING
        # TODO(bogdando) node's IPs should be populated as br-mgmt IPs, but now are hardcoded in templates
        signals.connect(node, node_sdn)
        node_sdn.connect_with_events(librarian, {'module': 'modules'}, {})
        evapi.add_dep(librarian.name, node_sdn.name, actions=('run', 'update'))

        signals.connect(node, node_sdn)
        node_sdn.connect_with_events(librarian, {'module': 'modules'}, {})
        evapi.add_dep(librarian.name, node_sdn.name, actions=('run', 'update'))

    return r

def setup_base(node, librarian):
    # MARIADB
    mariadb_service = cr.create('mariadb_service1', 'resources/mariadb_service', {
        'image': 'mariadb',
        'port': 3306
    })[0]

    node.connect(mariadb_service)

    # RABBIT
    rabbitmq_service = cr.create('rabbitmq_service1', 'resources/rabbitmq_service/', {
        'management_port': 15672,
        'port': 5672,
    })[0]
    openstack_vhost = cr.create('openstack_vhost', 'resources/rabbitmq_vhost/', {
        'vhost_name': 'openstack'
    })[0]

    openstack_rabbitmq_user = cr.create('openstack_rabbitmq_user', 'resources/rabbitmq_user/', {
        'user_name': 'openstack',
        'password': 'openstack_password'
    })[0]

    node.connect(rabbitmq_service)
    rabbitmq_service.connect_with_events(librarian, {'module': 'modules'}, {})
    evapi.add_dep(librarian.name, rabbitmq_service.name, actions=('run', 'update'))
    rabbitmq_service.connect(openstack_vhost)
    rabbitmq_service.connect(openstack_rabbitmq_user)
    openstack_vhost.connect(openstack_rabbitmq_user, {
        'vhost_name',
    })
    return {'mariadb_service': mariadb_service,
            'rabbitmq_service1': rabbitmq_service,
            'openstack_vhost': openstack_vhost,
            'openstack_rabbitmq_user': openstack_rabbitmq_user}

def setup_keystone(node, librarian, mariadb_service, openstack_rabbitmq_user):
    keystone_puppet = cr.create('keystone_puppet', 'resources/keystone_puppet', {})[0]

    keystone_puppet.connect_with_events(librarian, {'module': 'modules'}, {})
    evapi.add_dep(librarian.name, keystone_puppet.name, actions=('run', 'update'))

    evapi.add_dep(openstack_rabbitmq_user.name, keystone_puppet.name, actions=('run', 'update'))
    keystone_db = cr.create('keystone_db', 'resources/mariadb_db/', {
        'db_name': 'keystone_db',
        'login_user': 'root'
    })[0]
    keystone_db_user = cr.create('keystone_db_user', 'resources/mariadb_user/', {
        'user_name': 'keystone',
        'user_password': 'keystone',
    })[0]
    keystone_service_endpoint = cr.create('keystone_service_endpoint', 'resources/keystone_service_endpoint', {
        'endpoint_name': 'keystone',
        'adminurl': 'http://{{admin_ip}}:{{admin_port}}/v2.0',
        'internalurl': 'http://{{internal_ip}}:{{internal_port}}/v2.0',
        'publicurl': 'http://{{public_ip}}:{{public_port}}/v2.0',
        'description': 'OpenStack Identity Service',
        'type': 'identity'
    })[0]

    admin_tenant = cr.create('admin_tenant', 'resources/keystone_tenant', {
        'tenant_name': 'admin'
    })[0]
    admin_user = cr.create('admin_user', 'resources/keystone_user', {
        'user_name': 'admin',
        'user_password': 'admin'
    })[0]
    admin_role = cr.create('admin_role', 'resources/keystone_role', {
        'role_name': 'admin'
    })[0]
    services_tenant = cr.create('services_tenant', 'resources/keystone_tenant', {
        'tenant_name': 'services'
    })[0]
    admin_role_services = cr.create('admin_role_services', 'resources/keystone_role', {
        'role_name': 'admin'
    })[0]

    node.connect(keystone_db)
    node.connect(keystone_db_user)
    node.connect(keystone_puppet)
    mariadb_service.connect(keystone_db, {
        'port': 'login_port',
        'root_user': 'login_user',
        'root_password': 'login_password',
        'ip' : 'db_host',
    })
    keystone_db.connect(keystone_db_user, {
        'db_name',
        'login_port',
        'login_user',
        'login_password',
        'db_host'
    })

    node.connect(keystone_service_endpoint)
    keystone_puppet.connect(keystone_service_endpoint, {
        'admin_token': 'admin_token',
        'admin_port': ['admin_port', 'keystone_admin_port'],
        'ip': ['keystone_host', 'admin_ip', 'internal_ip', 'public_ip'],
        'port': ['internal_port', 'public_port'],
    })

    keystone_puppet.connect(admin_tenant)
    keystone_puppet.connect(admin_tenant, {
        'admin_port': 'keystone_port',
        'ip': 'keystone_host'
    })
    admin_tenant.connect(admin_user)
    admin_user.connect(admin_role)
    admin_tenant.connect(admin_role, { 'tenant_name' })

    admin_user.connect(admin_role_services)
    services_tenant.connect(admin_role_services, { 'tenant_name' })

    keystone_puppet.connect(services_tenant)
    keystone_puppet.connect(services_tenant, {
        'admin_port': 'keystone_port',
        'ip': 'keystone_host'
    })

    keystone_db.connect(keystone_puppet, {
        'db_name',
    })
    keystone_db_user.connect(keystone_puppet, {
        'user_name': 'db_user',
        'user_password': 'db_password',
    })
    mariadb_service.connect(keystone_puppet, {
        'ip': 'db_host',
        'port': 'db_port',
    })
    return {'keystone_puppet': keystone_puppet,
            'keystone_db': keystone_db,
            'keystone_db_user': keystone_db_user,
            'keystone_service_endpoint': keystone_service_endpoint,
            'admin_tenant': admin_tenant,
            'admin_user': admin_user,
            'admin_role': admin_role,
            'services_tenant': services_tenant,
            'admin_role_services': admin_role_services,
            }

def setup_openrc(node, keystone_puppet, admin_user):
    # OPENRC
    openrc = cr.create('openrc_file', 'resources/openrc_file', {})[0]

    node.connect(openrc)
    keystone_puppet.connect(openrc, {'ip': 'keystone_host', 'admin_port':'keystone_port'})
    admin_user.connect(openrc, {'user_name': 'user_name','user_password':'password', 'tenant_name': 'tenant'})
    return {'openrc_file' : openrc}

def setup_neutron(node, librarian, rabbitmq_service, openstack_rabbitmq_user, openstack_vhost):
    # NEUTRON
    # Deploy chain neutron -> (plugins) -> neutron_server -> ( agents )
    neutron_puppet = cr.create('neutron_puppet', 'resources/neutron_puppet', {
        'core_plugin': 'neutron.plugins.ml2.plugin.Ml2Plugin'
        })[0]

    node.connect(neutron_puppet)

    neutron_puppet.connect_with_events(librarian, {'module': 'modules'}, {})
    evapi.add_dep(librarian.name, neutron_puppet.name, actions=('run', 'update'))

    rabbitmq_service.connect(neutron_puppet, {
        'ip': 'rabbit_host',
        'port': 'rabbit_port'
    })
    openstack_rabbitmq_user.connect(neutron_puppet, {
        'user_name': 'rabbit_user',
        'password': 'rabbit_password'})
    openstack_vhost.connect(neutron_puppet, {
        'vhost_name': 'rabbit_virtual_host'})
    return {'neutron_puppet': neutron_puppet}

def setup_neutron_api(node, mariadb_service, admin_user, keystone_puppet, services_tenant, neutron_puppet):
    # NEUTRON PLUGIN AND  NEUTRON API (SERVER)
    neutron_plugins_ml2 = cr.create('neutron_plugins_ml2', 'resources/neutron_plugins_ml2_puppet', {})[0]
    node.connect(neutron_plugins_ml2)

    neutron_server_puppet = cr.create('neutron_server_puppet', 'resources/neutron_server_puppet', {
        'sync_db': True,
    })[0]
    evapi.add_dep(neutron_puppet.name, neutron_server_puppet.name, actions=('run',))
    evapi.add_dep(neutron_plugins_ml2.name, neutron_server_puppet.name, actions=('run',))
    evapi.add_dep(neutron_puppet.name, neutron_plugins_ml2.name, actions=('run',))

    neutron_db = cr.create('neutron_db', 'resources/mariadb_db/', {
        'db_name': 'neutron_db', 'login_user': 'root'})[0]
    neutron_db_user = cr.create('neutron_db_user', 'resources/mariadb_user/', {
        'user_name': 'neutron', 'user_password': 'neutron', 'login_user': 'root'})[0]
    neutron_keystone_user = cr.create('neutron_keystone_user', 'resources/keystone_user', {
        'user_name': 'neutron',
        'user_password': 'neutron'
    })[0]
    neutron_keystone_role = cr.create('neutron_keystone_role', 'resources/keystone_role', {
        'role_name': 'admin'
    })[0]
    evapi.add_dep(neutron_keystone_role.name, neutron_server_puppet.name, actions=('run',))
    neutron_keystone_service_endpoint = cr.create('neutron_keystone_service_endpoint', 'resources/keystone_service_endpoint', {
        'endpoint_name': 'neutron',
        'adminurl': 'http://{{admin_ip}}:{{admin_port}}',
        'internalurl': 'http://{{internal_ip}}:{{internal_port}}',
        'publicurl': 'http://{{public_ip}}:{{public_port}}',
        'description': 'OpenStack Network Service',
        'type': 'network'
    })[0]

    node.connect(neutron_db)
    node.connect(neutron_db_user)
    mariadb_service.connect(neutron_db, {
        'port': 'login_port',
        'root_password': 'login_password',
        'root_user': 'login_user',
        'ip' : 'db_host'})
    mariadb_service.connect(neutron_db_user, {'port': 'login_port', 'root_password': 'login_password'})
    neutron_db.connect(neutron_db_user, {'db_name', 'db_host'})
    neutron_db_user.connect(neutron_server_puppet, {
        'user_name':'db_user',
        'db_name':'db_name',
        'user_password':'db_password',
        'db_host' : 'db_host'})
    mariadb_service.connect(neutron_server_puppet, {
        'port': 'db_port',
        'ip' : 'db_host'})
    node.connect(neutron_server_puppet)
    admin_user.connect(neutron_server_puppet, {
        'user_name': 'auth_user',
        'user_password': 'auth_password',
        'tenant_name': 'auth_tenant'
    })
    keystone_puppet.connect(neutron_server_puppet, {
        'ip': 'auth_host',
        'port': 'auth_port'
    })
    services_tenant.connect(neutron_keystone_user)
    neutron_keystone_user.connect(neutron_keystone_role)
    keystone_puppet.connect(neutron_keystone_service_endpoint, {
        'ip': ['ip', 'keystone_host'],
        'admin_port': 'keystone_admin_port',
        'admin_token': 'admin_token',
    })
    neutron_puppet.connect(neutron_keystone_service_endpoint, {
        'ip': ['admin_ip', 'internal_ip', 'public_ip'],
        'bind_port': ['admin_port', 'internal_port', 'public_port'],
    })
    return {'neutron_server_puppet': neutron_server_puppet,
            'neutron_plugins_ml2': neutron_plugins_ml2,
            'neutron_db': neutron_db,
            'neutron_db_user': neutron_db_user,
            'neutron_keystone_user': neutron_keystone_user,
            'neutron_keystone_role': neutron_keystone_role,
            'neutron_keystone_service_endpoint': neutron_keystone_service_endpoint}

def setup_neutron_agent(node, neutron_server_puppet):
    # NEUTRON ML2 PLUGIN & ML2-OVS AGENT WITH GRE
    neutron_agents_ml2 = cr.create('neutron_agents_ml2', 'resources/neutron_agents_ml2_ovs_puppet', {
        # TODO(bogdando) these should come from the node network resource
        'enable_tunneling': True,
        'tunnel_types': ['gre'],
        'local_ip': '10.1.0.13' # should be the IP addr of the br-mesh int.
    })[0]
    node.connect(neutron_agents_ml2)
    evapi.add_dep(neutron_server_puppet.name, neutron_agents_ml2.name, actions=('run',))

    # NEUTRON DHCP, L3, metadata agents
    neutron_agents_dhcp = cr.create('neutron_agents_dhcp', 'resources/neutron_agents_dhcp_puppet', {})[0]
    node.connect(neutron_agents_dhcp)
    evapi.add_dep(neutron_server_puppet.name, neutron_agents_dhcp.name, actions=('run',))

    neutron_agents_l3 = cr.create('neutron_agents_l3', 'resources/neutron_agents_l3_puppet', {
        # TODO(bogdando) these should come from the node network resource
        'metadata_port': 8775,
        'external_network_bridge': 'br-floating',
    })[0]
    node.connect(neutron_agents_l3)
    evapi.add_dep(neutron_server_puppet.name, neutron_agents_l3.name, actions=('run',))

    neutron_agents_metadata = cr.create('neutron_agents_metadata', 'resources/neutron_agents_metadata_puppet', {
        'sh2ared_secret': 'secret',
    })[0]
    node.connect(neutron_agents_metadata)
    neutron_server_puppet.connect(neutron_agents_metadata, {
        'auth_host', 'auth_port', 'auth_password',
        'auth_tenant', 'auth_user',
    })
    return {'neutron_agents_ml2': neutron_agents_ml2,
            'neutron_agents_dhcp': neutron_agents_dhcp,
            'neutron_agents_metadata': neutron_agents_metadata}

def setup_neutron_compute(node, librarian, neutron_puppet, neutron_server_puppet):
    # NEUTRON FOR COMPUTE (node1)
    # Deploy chain neutron -> (plugins) -> ( agents )
    name = node.name
    neutron_puppet2 = cr.create('neutron_puppet_{}'.format(name), 'resources/neutron_puppet', {})[0]

    neutron_puppet2.connect_with_events(librarian, {'module': 'modules'}, {})
    evapi.add_dep(librarian.name, neutron_puppet2.name, actions=('run', 'update'))
    dep = evapi.Dep(librarian.name, 'update', state='SUCESS',
                child=neutron_puppet2.name, child_action='run')
    evapi.add_event(dep)

    node.connect(neutron_puppet2)
    neutron_puppet.connect(neutron_puppet2, {
        'rabbit_host', 'rabbit_port',
        'rabbit_user', 'rabbit_password',
        'rabbit_virtual_host',
        'package_ensure', 'core_plugin',
    })

    # NEUTRON OVS PLUGIN & AGENT WITH GRE FOR COMPUTE (node1)
    neutron_plugins_ml22 = cr.create('neutron_plugins_ml_{}'.format(name), 'resources/neutron_plugins_ml2_puppet', {})[0]
    node.connect(neutron_plugins_ml22)
    evapi.add_dep(neutron_puppet2.name, neutron_plugins_ml22.name, actions=('run',))
    evapi.add_dep(neutron_server_puppet.name, neutron_plugins_ml22.name, actions=('run',))

    neutron_agents_ml22 = cr.create('neutron_agents_ml_{}'.format(name), 'resources/neutron_agents_ml2_ovs_puppet', {
        # TODO(bogdando) these should come from the node network resource
        'enable_tunneling': True,
        'tunnel_types': ['gre'],
        'local_ip': '10.1.0.14' # Should be the IP addr of the br-mesh int.
    })[0]
    node.connect(neutron_agents_ml22)
    evapi.add_dep(neutron_puppet2.name, neutron_agents_ml22.name, actions=('run',))
    evapi.add_dep(neutron_server_puppet.name, neutron_agents_ml22.name, actions=('run',))

    return {'neutron_puppet2': neutron_puppet2,
            'neutron_plugins_ml22': neutron_plugins_ml22,
            'neutron_agents_ml22': neutron_agents_ml22}

def setup_cinder(node, librarian, rabbitmq_service, mariadb_service, keystone_puppet, admin_user, openstack_vhost, openstack_rabbitmq_user, services_tenant):
    # CINDER
    cinder_puppet = cr.create('cinder_puppet', 'resources/cinder_puppet', {})[0]
    cinder_db = cr.create('cinder_db', 'resources/mariadb_db/', {
        'db_name': 'cinder_db', 'login_user': 'root'})[0]
    cinder_db_user = cr.create('cinder_db_user', 'resources/mariadb_user/', {
        'user_name': 'cinder', 'user_password': 'cinder', 'login_user': 'root'})[0]
    cinder_keystone_user = cr.create('cinder_keystone_user', 'resources/keystone_user', {
        'user_name': 'cinder', 'user_password': 'cinder'})[0]
    cinder_keystone_role = cr.create('cinder_keystone_role', 'resources/keystone_role', {
        'role_name': 'admin'})[0]
    cinder_keystone_service_endpoint = cr.create(
        'cinder_keystone_service_endpoint',
        'resources/keystone_service_endpoint', {
            'endpoint_name': 'cinder',
            'adminurl': 'http://{{admin_ip}}:{{admin_port}}/v2/%(tenant_id)s',
            'internalurl': 'http://{{internal_ip}}:{{internal_port}}/v2/%(tenant_id)s',
            'publicurl': 'http://{{public_ip}}:{{public_port}}/v2/%(tenant_id)s',
            'description': 'OpenStack Block Storage Service', 'type': 'volumev2'})[0]

    node.connect(cinder_puppet)
    cinder_puppet.connect_with_events(librarian, {'module': 'modules'}, {})
    evapi.add_dep(librarian.name, cinder_puppet.name, actions=('run', 'update'))

    node.connect(cinder_db)
    node.connect(cinder_db_user)
    rabbitmq_service.connect(cinder_puppet, {'ip': 'rabbit_host', 'port': 'rabbit_port'})
    admin_user.connect(cinder_puppet, {'user_name': 'keystone_user', 'user_password': 'keystone_password', 'tenant_name': 'keystone_tenant'}) #?
    openstack_vhost.connect(cinder_puppet, {'vhost_name': 'rabbit_virtual_host'})
    openstack_rabbitmq_user.connect(cinder_puppet, {'user_name': 'rabbit_userid', 'password': 'rabbit_password'})
    mariadb_service.connect(cinder_db, {
        'port': 'login_port',
        'root_password': 'login_password',
        'root_user': 'login_user',
        'ip' : 'db_host'})
    mariadb_service.connect(cinder_db_user, {'port': 'login_port', 'root_password': 'login_password'})
    cinder_db.connect(cinder_db_user, {'db_name', 'db_host'})
    cinder_db_user.connect(cinder_puppet, {
        'user_name':'db_user',
        'db_name':'db_name',
        'user_password':'db_password'})
    mariadb_service.connect(cinder_puppet, {
        'port': 'db_port',
        'ip': 'db_host'})
    keystone_puppet.connect(cinder_puppet, {'ip': 'keystone_host', 'admin_port': 'keystone_port'}) #or non admin port?
    services_tenant.connect(cinder_keystone_user)
    cinder_keystone_user.connect(cinder_keystone_role)
    cinder_keystone_user.connect(cinder_puppet, {'user_name': 'keystone_user', 'tenant_name': 'keystone_tenant', 'user_password': 'keystone_password'})
    mariadb_service.connect(cinder_puppet, {'ip':'ip'})
    cinder_puppet.connect(cinder_keystone_service_endpoint, {
        'ip': ['ip', 'keystone_host', 'admin_ip', 'internal_ip', 'public_ip'],
        'port': ['admin_port', 'internal_port', 'public_port'],})
    keystone_puppet.connect(cinder_keystone_service_endpoint, {
        'admin_port': 'keystone_admin_port', 'admin_token': 'admin_token'})

    # CINDER GLANCE
    # Deploy chain: cinder_puppet -> cinder_glance -> ( cinder_api, cinder_scheduler, cinder_volume )
    cinder_glance_puppet = cr.create('cinder_glance_puppet', 'resources/cinder_glance_puppet', {})[0]
    node.connect(cinder_glance_puppet)
    evapi.add_dep(cinder_puppet.name, cinder_glance_puppet.name, actions=('run',))

    return {'cinder_puppet': cinder_puppet,
            'cinder_db': cinder_db,
            'cinder_db_user': cinder_db_user,
            'cinder_keystone_user': cinder_keystone_user,
            'cinder_keystone_role': cinder_keystone_role,
            'cinder_keystone_service_endpoint': cinder_keystone_service_endpoint,
            'cinder_glance_puppet': cinder_glance_puppet}

def setup_cinder_api(node, cinder_puppet):
    # CINDER API
    cinder_api_puppet = cr.create('cinder_api_puppet', 'resources/cinder_api_puppet', {})[0]
    node.connect(cinder_api_puppet)
    cinder_puppet.connect(cinder_api_puppet, {
        'keystone_password', 'keystone_tenant', 'keystone_user'})
    cinder_puppet.connect(cinder_api_puppet, {
        'keystone_host': 'keystone_auth_host',
        'keystone_port': 'keystone_auth_port'})
    evapi.add_react(cinder_puppet.name, cinder_api_puppet.name, actions=('update',))
    return {'cinder_api_puppet': cinder_api_puppet}

def setup_cinder_scheduler(node, cinder_puppet):
    # CINDER SCHEDULER
    cinder_scheduler_puppet = cr.create('cinder_scheduler_puppet', 'resources/cinder_scheduler_puppet', {})[0]
    node.connect(cinder_scheduler_puppet)
    cinder_puppet.connect(cinder_scheduler_puppet)
    evapi.add_react(cinder_puppet.name, cinder_scheduler_puppet.name, actions=('update',))
    return {'cinder_scheduler_puppet': cinder_scheduler_puppet}

def setup_cinder_volume(node, cinder_puppet):
    # CINDER VOLUME
    cinder_volume = cr.create('cinder_volume_{}'.format(node.name), 'resources/volume_group',
            {'path': '/root/cinder.img', 'volume_name': 'cinder-volume'})[0]
    node.connect(cinder_volume)

    cinder_volume_puppet = cr.create('cinder_volume_puppet', 'resources/cinder_volume_puppet', {})[0]
    node.connect(cinder_volume_puppet)
    cinder_puppet.connect(cinder_volume_puppet)
    evapi.add_react(cinder_puppet.name, cinder_volume_puppet.name, actions=('update',))
    cinder_volume.connect(cinder_volume_puppet, {'volume_name': 'volume_group'})
    return {'cinder_volume_puppet': cinder_volume_puppet}

def setup_nova(node, librarian, mariadb_service, rabbitmq_service, admin_user, openstack_vhost, services_tenant, keystone_puppet, openstack_rabbitmq_user):
    # NOVA
    nova_puppet = cr.create('nova_puppet', 'resources/nova_puppet', {})[0]
    nova_db = cr.create('nova_db', 'resources/mariadb_db/', {
        'db_name': 'nova_db',
        'login_user': 'root'})[0]
    nova_db_user = cr.create('nova_db_user', 'resources/mariadb_user/', {
        'user_name': 'nova',
        'user_password': 'nova',
        'login_user': 'root'})[0]
    nova_keystone_user = cr.create('nova_keystone_user', 'resources/keystone_user', {
        'user_name': 'nova',
        'user_password': 'nova'})[0]
    nova_keystone_role = cr.create('nova_keystone_role', 'resources/keystone_role', {
        'role_name': 'admin'})[0]
    nova_keystone_service_endpoint = cr.create('nova_keystone_service_endpoint', 'resources/keystone_service_endpoint', {
        'endpoint_name': 'nova',
        'adminurl': 'http://{{admin_ip}}:{{admin_port}}/v2/%(tenant_id)s',
        'internalurl': 'http://{{internal_ip}}:{{internal_port}}/v2/%(tenant_id)s',
        'publicurl': 'http://{{public_ip}}:{{public_port}}/v2/%(tenant_id)s',
        'description': 'OpenStack Compute Service',
        'type': 'compute'})[0]

    node.connect(nova_puppet)
    nova_puppet.connect_with_events(librarian, {'module': 'modules'}, {})
    evapi.add_dep(librarian.name, nova_puppet.name, actions=('run', 'update'))

    node.connect(nova_db)
    node.connect(nova_db_user)
    mariadb_service.connect(nova_db, {
        'port': 'login_port',
        'root_password': 'login_password',
        'root_user': 'login_user',
        'ip' : 'db_host'})
    mariadb_service.connect(nova_db_user, {
        'port': 'login_port',
        'root_password': 'login_password'})
    admin_user.connect(nova_puppet, {'user_name': 'keystone_user', 'user_password': 'keystone_password', 'tenant_name': 'keystone_tenant'}) #?
    openstack_vhost.connect(nova_puppet, {'vhost_name': 'rabbit_virtual_host'})
    nova_db.connect(nova_db_user, {'db_name', 'db_host'})
    services_tenant.connect(nova_keystone_user)
    nova_keystone_user.connect(nova_keystone_role)
    keystone_puppet.connect(nova_puppet, {
        'ip': 'keystone_host',
        'admin_port': 'keystone_port'})
    nova_keystone_user.connect(nova_puppet, {
        'user_name': 'keystone_user',
        'tenant_name': 'keystone_tenant',
        'user_password': 'keystone_password'})
    rabbitmq_service.connect(nova_puppet, {
        'ip': 'rabbit_host', 'port': 'rabbit_port'})
    openstack_rabbitmq_user.connect(nova_puppet, {
        'user_name': 'rabbit_userid',
        'password': 'rabbit_password'})
    keystone_puppet.connect(nova_keystone_service_endpoint, {
        'ip': 'keystone_host',
        'admin_port': 'keystone_admin_port',
        'admin_token': 'admin_token'})
    mariadb_service.connect(nova_puppet, {
        'ip':'db_host',
        'port': 'db_port'})
    nova_db_user.connect(nova_puppet, {
        'user_name':'db_user',
        'db_name':'db_name',
        'user_password':'db_password'})
    nova_puppet.connect(nova_keystone_service_endpoint, {
        'ip': ['ip', 'keystone_host', 'public_ip', 'internal_ip', 'admin_ip'],
        'port': ['admin_port', 'internal_port', 'public_port'],
    })
    return {'nova_puppet': nova_puppet,
            'nova_db': nova_db,
            'nova_db_user': nova_db_user,
            'nova_keystone_user': nova_keystone_user,
            'nova_keystone_role': nova_keystone_role,
            'nova_keystone_service_endpoint': nova_keystone_service_endpoint}

def setup_nova_api(node, nova_puppet, neutron_agents_metadata):
    # NOVA API
    nova_api_puppet = cr.create('nova_api_puppet', 'resources/nova_api_puppet', {})[0]
    node.connect(nova_api_puppet)
    nova_puppet.connect(nova_api_puppet, {
        'keystone_tenant': 'admin_tenant_name',
        'keystone_user': 'admin_user',
        'keystone_password': 'admin_password',
        'keystone_host': 'auth_host',
        'keystone_port': 'auth_port'})
    evapi.add_react(nova_puppet.name, nova_api_puppet.name, actions=('update',))
    nova_api_puppet.connect(neutron_agents_metadata, {'ip': 'metadata_ip'})
    return {'nova_api_puppet': nova_api_puppet}

def setup_nova_conductor(node, nova_puppet, nova_api_puppet):
    # NOVA CONDUCTOR
    nova_conductor_puppet = cr.create('nova_conductor_puppet', 'resources/nova_conductor_puppet', {})[0]
    node.connect(nova_conductor_puppet)
    nova_puppet.connect(nova_conductor_puppet)
    evapi.add_dep(nova_api_puppet.name, nova_conductor_puppet.name, actions=('run',))
    evapi.add_react(nova_puppet.name, nova_conductor_puppet.name, actions=('update',))
    return {'nova_conductor': nova_conductor_puppet}

def setup_nova_scheduler(node, nova_puppet, nova_api_puppet):
    # NOVA SCHEDULER
    # NOTE(bogdando) Generic service is used. Package and service names for Ubuntu case
    #   come from https://github.com/openstack/puppet-nova/blob/5.1.0/manifests/params.pp
    nova_scheduler_puppet = cr.create('nova_scheduler_puppet', 'resources/nova_generic_service_puppet', {
        'title' : 'scheduler', 'package_name': 'nova-scheduler', 'service_name': 'nova-scheduler',
    })[0]
    node.connect(nova_scheduler_puppet)
    evapi.add_dep(nova_puppet.name, nova_scheduler_puppet.name, actions=('run',))
    evapi.add_dep(nova_api_puppet.name, nova_scheduler_puppet.name, actions=('run',))
    evapi.add_react(nova_puppet.name, nova_scheduler_puppet.name, actions=('update',))
    return {'nova_scheduler_puppet': nova_scheduler_puppet}

def setup_nova_compute(node, librarian, nova_puppet, nova_api_puppet, neutron_server_puppet, neutron_keystone_service_endpoint, glance_api_puppet):
    # NOVA COMPUTE
    # Deploy chain (nova, node_networking(TODO)) -> (nova_compute_libvirt, nova_neutron) -> nova_compute
    name = node.name
    nova_compute_puppet = cr.create('nova_compute_puppet_{}'.format(name), 'resources/nova_compute_puppet', {})[0]
    # TODO (bogdando) figure out how to use it for multiple glance api servers
    nova_puppet2 = cr.create('nova_puppet_{}'.format(name), 'resources/nova_puppet', {
        'glance_api_servers': '{{glance_api_servers_host}}:{{glance_api_servers_port}}'
        })[0]
    nova_puppet.connect(nova_puppet2, {
        'ensure_package', 'rabbit_host',
        'rabbit_password', 'rabbit_port', 'rabbit_userid',
        'rabbit_virtual_host', 'db_user', 'db_password',
        'db_name', 'db_host', 'keystone_password',
        'keystone_port', 'keystone_host', 'keystone_tenant',
        'keystone_user',
    })
    # TODO(bogdando): Make a connection for nova_puppet2.glance_api_servers = "glance_api_puppet.ip:glance_api_puppet.bind_port"
    node.connect(nova_puppet2)
    nova_puppet2.connect_with_events(librarian, {'module': 'modules'}, {})
    evapi.add_dep(librarian.name, nova_puppet2.name, actions=('run', 'update'))
    dep = evapi.Dep(librarian.name, 'update', state='SUCESS',
                child=nova_puppet2.name, child_action='run')
    evapi.add_event(dep)

    node.connect(nova_compute_puppet)
    evapi.add_dep(nova_puppet2.name, nova_compute_puppet.name, actions=('run',))
    evapi.add_dep(nova_api_puppet.name, nova_compute_puppet.name, actions=('run',))
    evapi.add_react(nova_puppet2.name, nova_compute_puppet.name, actions=('run', 'update'))

    # NOVA COMPUTE LIBVIRT, NOVA_NEUTRON
    # NOTE(bogdando): changes nova config, so should notify nova compute service
    nova_compute_libvirt_puppet = cr.create('nova_compute_libvirt_puppet_{}'.format(name), 'resources/nova_compute_libvirt_puppet', {})[0]
    node.connect(nova_compute_libvirt_puppet)
    evapi.add_dep(nova_puppet2.name, nova_compute_libvirt_puppet.name, actions=('run',))
    evapi.add_dep(nova_api_puppet.name, nova_compute_libvirt_puppet.name, actions=('run',))

    # compute configuration for neutron, use http auth/endpoint protocols, keystone v2 auth hardcoded for the resource
    nova_neutron_puppet = cr.create('nova_neutron_puppet_{}'.format(name), 'resources/nova_neutron_puppet', {})[0]
    node.connect(nova_neutron_puppet)
    evapi.add_dep(nova_puppet2.name, nova_neutron_puppet.name, actions=('run',))
    evapi.add_dep(nova_api_puppet.name, nova_neutron_puppet.name, actions=('run',))
    neutron_server_puppet.connect(nova_neutron_puppet, {
        'auth_password': 'neutron_admin_password',
        'auth_user': 'neutron_admin_username',
        'auth_type': 'neutron_auth_strategy',
        'auth_host': 'auth_host', 'auth_port': 'auth_port',
        'auth_protocol': 'auth_protocol',
    })
    neutron_keystone_service_endpoint.connect(nova_neutron_puppet, {
        'internal_ip':'neutron_endpoint_host',
        'internal_port':'neutron_endpoint_port',
    })
    # Update glance_api_service for nova compute
    glance_api_puppet.connect(nova_puppet2, {
        'ip': 'glance_api_servers_host',
        'bind_port': 'glance_api_servers_port'
    })

    # signals.connect(keystone_puppet, nova_network_puppet, {'ip': 'keystone_host', 'port': 'keystone_port'})
    # signals.connect(keystone_puppet, nova_keystone_service_endpoint, {'ip': 'keystone_host', 'admin_port': 'keystone_port', 'admin_token': 'admin_token'})
    # signals.connect(rabbitmq_service1, nova_network_puppet, {'ip': 'rabbitmq_host', 'port': 'rabbitmq_port'})
    return {'nova_compute_puppet': nova_compute_puppet,
            'nova_puppet2': nova_puppet2,
            'nova_compute_libvirt_puppet': nova_compute_libvirt_puppet,
            'nova_neutron_puppet': nova_neutron_puppet,
            'neutron_server_puppet': neutron_server_puppet}

def setup_glance_api(node, librarian, mariadb_service, admin_user, keystone_puppet, services_tenant, cinder_glance_puppet):
    # GLANCE (base and API)
    glance_api_puppet = cr.create('glance_api_puppet', 'resources/glance_puppet', {})[0]
    glance_db_user = cr.create('glance_db_user', 'resources/mariadb_user/', {
        'user_name': 'glance', 'user_password': 'glance', 'login_user': 'root'})[0]
    glance_db = cr.create('glance_db', 'resources/mariadb_db/', {
        'db_name': 'glance', 'login_user': 'root'})[0]
    glance_keystone_user = cr.create('glance_keystone_user', 'resources/keystone_user', {
        'user_name': 'glance', 'user_password': 'glance123'})[0]
    glance_keystone_role = cr.create('glance_keystone_role', 'resources/keystone_role', {
        'role_name': 'admin'})[0]
    glance_keystone_service_endpoint = cr.create(
        'glance_keystone_service_endpoint',
        'resources/keystone_service_endpoint', {
            'endpoint_name': 'glance',
            'adminurl': 'http://{{admin_ip}}:{{admin_port}}',
            'internalurl': 'http://{{internal_ip}}:{{internal_port}}',
            'publicurl': 'http://{{public_ip}}:{{public_port}}',
            'description': 'OpenStack Image Service', 'type': 'image'})[0]

    node.connect(glance_api_puppet)
    glance_api_puppet.connect_with_events(librarian, {'module': 'modules'}, {})
    evapi.add_dep(librarian.name, glance_api_puppet.name, actions=('run', 'update'))

    node.connect(glance_db)
    node.connect(glance_db_user)
    admin_user.connect(glance_api_puppet, {
        'user_name': 'keystone_user', 'user_password': 'keystone_password',
        'tenant_name': 'keystone_tenant'}) #?
    mariadb_service.connect(glance_db, {
        'port': 'login_port',
        'root_password': 'login_password',
        'root_user': 'login_user',
        'ip' : 'db_host'})
    mariadb_service.connect(glance_db_user, {'port': 'login_port', 'root_password': 'login_password'})
    glance_db.connect(glance_db_user, {'db_name', 'db_host'})
    glance_db_user.connect(glance_api_puppet, {
        'user_name':'db_user',
        'db_name':'db_name',
        'user_password':'db_password',
        'db_host' : 'db_host'})
    mariadb_service.connect(glance_api_puppet,{
        'port': 'db_port',
        'ip': 'db_host'})
    keystone_puppet.connect(glance_api_puppet, {'ip': 'keystone_host', 'admin_port': 'keystone_port'}) #or non admin port?
    services_tenant.connect(glance_keystone_user)
    glance_keystone_user.connect(glance_keystone_role)
    glance_keystone_user.connect(glance_api_puppet, {
        'user_name': 'keystone_user', 'tenant_name': 'keystone_tenant',
        'user_password': 'keystone_password'})
    mariadb_service.connect(glance_api_puppet, {'ip':'ip'})
    glance_api_puppet.connect(glance_keystone_service_endpoint, {
        'ip': ['ip', 'keystone_host', 'admin_ip', 'internal_ip', 'public_ip'],
        'bind_port': ['admin_port', 'internal_port', 'public_port'],})
    keystone_puppet.connect(glance_keystone_service_endpoint, {
        'admin_port': 'keystone_admin_port', 'admin_token': 'admin_token'})

    # Update glance_api_service for cinder
    glance_api_puppet.connect(cinder_glance_puppet, {
        'ip': 'glance_api_servers_host',
        'bind_port': 'glance_api_servers_port'
    })
    return {'glance_api_puppet': glance_api_puppet,
            'glance_db_user': glance_db_user,
            'glance_db': glance_db,
            'glance_keystone_user': glance_keystone_user,
            'glance_keystone_role': glance_keystone_role,
            'glance_keystone_service_endpoint': glance_keystone_service_endpoint}

def setup_glance_registry(node, glance_api_puppet):
    # GLANCE REGISTRY
    glance_registry_puppet = cr.create('glance_registry_puppet', 'resources/glance_registry_puppet', {})[0]
    node.connect(glance_registry_puppet)
    glance_api_puppet.connect(glance_registry_puppet)
    evapi.add_react(glance_api_puppet.name, glance_registry_puppet.name, actions=('update',))
    # API and registry should not listen same ports
    # should not use the same log destination and a pipeline,
    # so disconnect them and restore the defaults
    signals.disconnect_receiver_by_input(glance_registry_puppet, 'bind_port')
    signals.disconnect_receiver_by_input(glance_registry_puppet, 'log_file')
    signals.disconnect_receiver_by_input(glance_registry_puppet, 'pipeline')
    glance_registry_puppet.update({
        'bind_port': 9191,
        'log_file': '/var/log/glance/registry.log',
        'pipeline': 'keystone',
    })
    return {'glance_registry_puppet': glance_registry_puppet}


def validate():
    has_errors = False
    for r in locals().values():
        if not isinstance(r, resource.Resource):
            continue

        print 'Validating {}'.format(r.name)
        errors = validation.validate_resource(r)
        if errors:
            has_errors = True
            print 'ERROR: %s: %s' % (r.name, errors)

    if has_errors:
        sys.exit(1)


def create_controller(node):
    r = {r.name: r for r in resource.load_all()}
    librarian_node = 'librarian_{}'.format(node)

    r.update(setup_base(r[node], r[librarian_node]))
    r.update(setup_keystone(r[node], r[librarian_node],
                            r['mariadb_service'], r['openstack_rabbitmq_user']))
    r.update(setup_openrc(r[node], r['keystone_puppet'], r['admin_user']))
    r.update(setup_neutron(r[node], r['librarian_{}'.format(node)], r['rabbitmq_service1'],
                           r['openstack_rabbitmq_user'], r['openstack_vhost']))
    r.update(setup_neutron_api(r[node], r['mariadb_service'], r['admin_user'],
                               r['keystone_puppet'], r['services_tenant'], r['neutron_puppet']))
    r.update(setup_neutron_agent(r[node], r['neutron_server_puppet']))
    r.update(setup_cinder(r[node], r['librarian_{}'.format(node)], r['rabbitmq_service1'],
                          r['mariadb_service'], r['keystone_puppet'], r['admin_user'],
                          r['openstack_vhost'], r['openstack_rabbitmq_user'], r['services_tenant']))
    r.update(setup_cinder_api(r[node], r['cinder_puppet']))
    r.update(setup_cinder_scheduler(r[node], r['cinder_puppet']))
    r.update(setup_cinder_volume(r[node], r['cinder_puppet']))
    r.update(setup_nova(r[node], r['librarian_{}'.format(node)], r['mariadb_service'], r['rabbitmq_service1'],
                        r['admin_user'], r['openstack_vhost'], r['services_tenant'],
                        r['keystone_puppet'], r['openstack_rabbitmq_user']))
    r.update(setup_nova_api(r[node], r['nova_puppet'], r['neutron_agents_metadata']))
    r.update(setup_nova_conductor(r[node], r['nova_puppet'], r['nova_api_puppet']))
    r.update(setup_nova_scheduler(r[node], r['nova_puppet'], r['nova_api_puppet']))
    r.update(setup_glance_api(r[node], r['librarian_{}'.format(node)], r['mariadb_service'], r['admin_user'],
                              r['keystone_puppet'], r['services_tenant'],
                              r['cinder_glance_puppet']))
    r.update(setup_glance_registry(r[node], r['glance_api_puppet']))
    return r

def create_compute(node):
    r = {r.name: r for r in resource.load_all()}
    librarian_node = 'librarian_{}'.format(node)
    res = {}
    res.update(setup_neutron_compute(r[node], r[librarian_node], r['neutron_puppet'], r['neutron_server_puppet']))
    res.update(setup_nova_compute(r[node], r[librarian_node], r['nova_puppet'], r['nova_api_puppet'],
                                  r['neutron_server_puppet'], r['neutron_keystone_service_endpoint'], r['glance_api_puppet']))
    return r

@click.command()
def create_all():
    ModelMeta.remove_all()
    r = prepare_nodes(2)
    r.update(create_controller('node1'))
    r.update(create_compute('node2'))
    print '\n'.join(r.keys())

@click.command()
@click.argument('nodes_count')
def prepare(nodes_count):
    r = prepare_nodes(nodes_count)
    print '\n'.join(r.keys())

@click.command()
@click.argument('node')
def add_compute(node):
    r = create_compute(node)
    print '\n'.join(r.keys())

@click.command()
@click.argument('node')
def add_controller(node):
    r = create_controller(node)
    print '\n'.join(r.keys())

@click.command()
def clear():
    ModelMeta.remove_all()


if __name__ == '__main__':
    main.add_command(create_all)
    main.add_command(prepare)
    main.add_command(add_controller)
    main.add_command(add_compute)
    main.add_command(clear)
    main()

    if PROFILE:
        pr.disable()
        s = StringIO.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print s.getvalue()
        sys.exit(0)
