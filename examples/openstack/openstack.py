#!/usr/bin/env python

import click
import sys
import time

from solar.core import actions
from solar.core import resource
from solar.core import signals
from solar.core import validation
from solar.core.resource import virtual_resource as vr
from solar import errors
from solar import events as evapi

from solar.interfaces.db import get_db


PROFILE = False
#PROFILE = True


if PROFILE:
    import StringIO
    import cProfile
    import pstats

    pr = cProfile.Profile()


GIT_PUPPET_LIBS_URL = 'https://github.com/CGenie/puppet-libs-resource'


# TODO
# Resource for repository OR puppet apt-module in run.pp
# add-apt-repository cloud-archive:juno
# To discuss: install stuff in Docker container

# NOTE
# No copy of manifests, pull from upstream (implemented in the puppet handler)
# Official puppet manifests, not fuel-library


db = get_db()


@click.group()
def main():
    pass


def setup_resources():
    db.clear()

    if PROFILE:
        pr.enable()

    node1, node2 = vr.create('nodes', 'templates/nodes.yaml', {})

    # MARIADB
    mariadb_service1 = vr.create('mariadb_service1', 'resources/mariadb_service', {
        'image': 'mariadb',
        'port': 3306
    })[0]

    signals.connect(node1, mariadb_service1)

    # RABBIT
    rabbitmq_service1 = vr.create('rabbitmq_service1', 'resources/rabbitmq_service/', {
        'management_port': 15672,
        'port': 5672,
    })[0]
    openstack_vhost = vr.create('openstack_vhost', 'resources/rabbitmq_vhost/', {
        'vhost_name': 'openstack'
    })[0]

    openstack_rabbitmq_user = vr.create('openstack_rabbitmq_user', 'resources/rabbitmq_user/', {
        'user_name': 'openstack',
        'password': 'openstack_password'
    })[0]

    signals.connect(node1, rabbitmq_service1)
    signals.connect(rabbitmq_service1, openstack_vhost)
    signals.connect(rabbitmq_service1, openstack_rabbitmq_user)
    signals.connect(openstack_vhost, openstack_rabbitmq_user, {
        'vhost_name',
    })

    # KEYSTONE
    keystone_puppet = vr.create('keystone_puppet', 'resources/keystone_puppet', {})[0]
    evapi.add_dep(rabbitmq_service1.name, keystone_puppet.name, actions=('run', 'update'))
    keystone_db = vr.create('keystone_db', 'resources/mariadb_db/', {
        'db_name': 'keystone_db',
        'login_user': 'root'
    })[0]
    keystone_db_user = vr.create('keystone_db_user', 'resources/mariadb_user/', {
        'user_name': 'keystone',
        'user_password': 'keystone',
    })[0]
    keystone_service_endpoint = vr.create('keystone_service_endpoint', 'resources/keystone_service_endpoint', {
        'endpoint_name': 'keystone',
        'adminurl': 'http://{{admin_ip}}:{{admin_port}}/v2.0',
        'internalurl': 'http://{{internal_ip}}:{{internal_port}}/v2.0',
        'publicurl': 'http://{{public_ip}}:{{public_port}}/v2.0',
        'description': 'OpenStack Identity Service',
        'type': 'identity'
    })[0]

    admin_tenant = vr.create('admin_tenant', 'resources/keystone_tenant', {
        'tenant_name': 'admin'
    })[0]
    admin_user = vr.create('admin_user', 'resources/keystone_user', {
        'user_name': 'admin',
        'user_password': 'admin'
    })[0]
    admin_role = vr.create('admin_role', 'resources/keystone_role', {
        'role_name': 'admin'
    })[0]
    services_tenant = vr.create('services_tenant', 'resources/keystone_tenant', {
        'tenant_name': 'services'
    })[0]
    admin_role_services = vr.create('admin_role_services', 'resources/keystone_role', {
        'role_name': 'admin'
    })[0]

    signals.connect(node1, keystone_db)
    signals.connect(node1, keystone_db_user)
    signals.connect(node1, keystone_puppet)
    signals.connect(mariadb_service1, keystone_db, {
        'port': 'login_port',
        'root_user': 'login_user',
        'root_password': 'login_password',
        'ip' : 'db_host',
    })
    signals.connect(keystone_db, keystone_db_user, {
        'db_name',
        'login_port',
        'login_user',
        'login_password',
        'db_host'
    })

    signals.connect(node1, keystone_service_endpoint)
    signals.connect(keystone_puppet, keystone_service_endpoint, {
        'admin_token': 'admin_token',
        'admin_port': ['admin_port', 'keystone_admin_port'],
        'ip': ['keystone_host', 'admin_ip', 'internal_ip', 'public_ip'],
        'port': ['internal_port', 'public_port'],
    })

    signals.connect(keystone_puppet, admin_tenant)
    signals.connect(keystone_puppet, admin_tenant, {
        'admin_port': 'keystone_port',
        'ip': 'keystone_host'
    })
    signals.connect(admin_tenant, admin_user)
    signals.connect(admin_user, admin_role)
    signals.connect(admin_user, admin_role_services)
    signals.connect(services_tenant, admin_role_services, { 'tenant_name' })

    signals.connect(keystone_puppet, services_tenant)
    signals.connect(keystone_puppet, services_tenant, {
        'admin_port': 'keystone_port',
        'ip': 'keystone_host'
    })

    signals.connect(keystone_db, keystone_puppet, {
        'db_name',
    })
    signals.connect(keystone_db_user, keystone_puppet, {
        'user_name': 'db_user',
        'user_password': 'db_password',
        'db_host' : 'db_host'
    })

    # OPENRC
    openrc = vr.create('openrc_file', 'resources/openrc_file', {})[0]

    signals.connect(node1, openrc)
    signals.connect(keystone_puppet, openrc, {'ip': 'keystone_host', 'admin_port':'keystone_port'})
    signals.connect(admin_user, openrc, {'user_name': 'user_name','user_password':'password', 'tenant_name': 'tenant'})

    # NEUTRON
    # Deploy chain neutron -> (plugins) -> neutron_server -> ( agents )
    neutron_puppet = vr.create('neutron_puppet', 'resources/neutron_puppet', {
        'core_plugin': 'neutron.plugins.ml2.plugin.Ml2Plugin'
        })[0]
    signals.connect(node1, neutron_puppet)
    signals.connect(rabbitmq_service1, neutron_puppet, {
        'ip': 'rabbit_host',
        'port': 'rabbit_port'
    })
    signals.connect(openstack_rabbitmq_user, neutron_puppet, {
        'user_name': 'rabbit_user',
        'password': 'rabbit_password'})
    signals.connect(openstack_vhost, neutron_puppet, {
        'vhost_name': 'rabbit_virtual_host'})

    # NEUTRON API (SERVER)
    neutron_server_puppet = vr.create('neutron_server_puppet', 'resources/neutron_server_puppet', {
        'sync_db': True,
    })[0]
    neutron_db = vr.create('neutron_db', 'resources/mariadb_db/', {
        'db_name': 'neutron_db', 'login_user': 'root'})[0]
    neutron_db_user = vr.create('neutron_db_user', 'resources/mariadb_user/', {
        'user_name': 'neutron', 'user_password': 'neutron', 'login_user': 'root'})[0]
    neutron_keystone_user = vr.create('neutron_keystone_user', 'resources/keystone_user', {
        'user_name': 'neutron',
        'user_password': 'neutron'
    })[0]
    neutron_keystone_role = vr.create('neutron_keystone_role', 'resources/keystone_role', {
        'role_name': 'admin'
    })[0]
    neutron_keystone_service_endpoint = vr.create('neutron_keystone_service_endpoint', 'resources/keystone_service_endpoint', {
        'endpoint_name': 'neutron',
        'adminurl': 'http://{{admin_ip}}:{{admin_port}}',
        'internalurl': 'http://{{internal_ip}}:{{internal_port}}',
        'publicurl': 'http://{{public_ip}}:{{public_port}}',
        'description': 'OpenStack Network Service',
        'type': 'network'
    })[0]

    signals.connect(node1, neutron_db)
    signals.connect(node1, neutron_db_user)
    signals.connect(mariadb_service1, neutron_db, {
        'port': 'login_port',
        'root_password': 'login_password',
        'root_user': 'login_user',
        'ip' : 'db_host'})
    signals.connect(mariadb_service1, neutron_db_user, {'port': 'login_port', 'root_password': 'login_password'})
    signals.connect(neutron_db, neutron_db_user, {'db_name', 'db_host'})
    signals.connect(neutron_db_user, neutron_server_puppet, {
        'user_name':'db_user',
        'db_name':'db_name',
        'user_password':'db_password',
        'db_host' : 'db_host'})
    signals.connect(node1, neutron_server_puppet)
    signals.connect(admin_user, neutron_server_puppet, {
        'user_name': 'auth_user',
        'user_password': 'auth_password',
        'tenant_name': 'auth_tenant'
    })
    signals.connect(keystone_puppet, neutron_server_puppet, {
        'ip': 'auth_host',
        'port': 'auth_port'
    })
    signals.connect(services_tenant, neutron_keystone_user)
    signals.connect(neutron_keystone_user, neutron_keystone_role)
    signals.connect(keystone_puppet, neutron_keystone_service_endpoint, {
        'ip': ['ip', 'keystone_host'],
        'ssh_key': 'ssh_key',
        'ssh_user': 'ssh_user',
        'admin_port': 'keystone_admin_port',
        'admin_token': 'admin_token',
    })
    signals.connect(neutron_puppet, neutron_keystone_service_endpoint, {
        'ip': ['admin_ip', 'internal_ip', 'public_ip'],
        'bind_port': ['admin_port', 'internal_port', 'public_port'],
    })

    # NEUTRON ML2 PLUGIN & ML2-OVS AGENT WITH GRE
    neutron_plugins_ml2 = vr.create('neutron_plugins_ml2', 'resources/neutron_plugins_ml2_puppet', {})[0]
    signals.connect(node1, neutron_plugins_ml2)
    neutron_agents_ml2 = vr.create('neutron_agents_ml2', 'resources/neutron_agents_ml2_ovs_puppet', {
        # TODO(bogdando) these should come from the node network resource
        'enable_tunneling': True,
        'tunnel_types': ['gre'],
        'local_ip': '10.1.0.13' # should be the IP addr of the br-mesh int.
    })[0]
    signals.connect(node1, neutron_agents_ml2)

    # NEUTRON DHCP, L3, metadata agents
    neutron_agents_dhcp = vr.create('neutron_agents_dhcp', 'resources/neutron_agents_dhcp_puppet', {})[0]
    signals.connect(node1, neutron_agents_dhcp)
    neutron_agents_l3 = vr.create('neutron_agents_l3', 'resources/neutron_agents_l3_puppet', {
        # TODO(bogdando) these should come from the node network resource
        'metadata_port': 8775,
        'external_network_bridge': 'br-floating',
    })[0]
    signals.connect(node1, neutron_agents_l3)
    neutron_agents_metadata = vr.create('neutron_agents_metadata', 'resources/neutron_agents_metadata_puppet', {
        'shared_secret': 'secret',
    })[0]
    signals.connect(node1, neutron_agents_metadata)
    signals.connect(neutron_server_puppet, neutron_agents_metadata, {
        'auth_host', 'auth_port', 'auth_password',
        'auth_tenant', 'auth_user',
    })

    # NEUTRON FOR COMPUTE (node2)
    # Deploy chain neutron -> (plugins) -> ( agents )
    neutron_puppet2 = vr.create('neutron_puppet2', 'resources/neutron_puppet', {})[0]
    signals.connect(node2, neutron_puppet2)
    signals.connect(neutron_puppet, neutron_puppet2, {
        'rabbit_host', 'rabbit_port',
        'rabbit_user', 'rabbit_password',
        'rabbit_virtual_host',
        'package_ensure', 'core_plugin',
    })

    # NEUTRON OVS PLUGIN & AGENT WITH GRE FOR COMPUTE (node2)
    neutron_plugins_ml22 = vr.create('neutron_plugins_ml22', 'resources/neutron_plugins_ml2_puppet', {})[0]
    signals.connect(node2, neutron_plugins_ml22)
    neutron_agents_ml22 = vr.create('neutron_agents_ml22', 'resources/neutron_agents_ml2_ovs_puppet', {
        # TODO(bogdando) these should come from the node network resource
        'enable_tunneling': True,
        'tunnel_types': ['gre'],
        'local_ip': '10.1.0.14' # Should be the IP addr of the br-mesh int.
    })[0]
    signals.connect(node2, neutron_agents_ml22)

    # CINDER
    cinder_puppet = vr.create('cinder_puppet', 'resources/cinder_puppet', {})[0]
    cinder_db = vr.create('cinder_db', 'resources/mariadb_db/', {
        'db_name': 'cinder_db', 'login_user': 'root'})[0]
    cinder_db_user = vr.create('cinder_db_user', 'resources/mariadb_user/', {
        'user_name': 'cinder', 'user_password': 'cinder', 'login_user': 'root'})[0]
    cinder_keystone_user = vr.create('cinder_keystone_user', 'resources/keystone_user', {
        'user_name': 'cinder', 'user_password': 'cinder'})[0]
    cinder_keystone_role = vr.create('cinder_keystone_role', 'resources/keystone_role', {
        'role_name': 'admin'})[0]
    cinder_keystone_service_endpoint = vr.create(
        'cinder_keystone_service_endpoint',
        'resources/keystone_service_endpoint', {
            'endpoint_name': 'cinder',
            'adminurl': 'http://{{admin_ip}}:{{admin_port}}/v2/%(tenant_id)s',
            'internalurl': 'http://{{internal_ip}}:{{internal_port}}/v2/%(tenant_id)s',
            'publicurl': 'http://{{public_ip}}:{{public_port}}/v2/%(tenant_id)s',
            'description': 'OpenStack Block Storage Service', 'type': 'volumev2'})[0]

    signals.connect(node1, cinder_puppet)
    signals.connect(node1, cinder_db)
    signals.connect(node1, cinder_db_user)
    signals.connect(rabbitmq_service1, cinder_puppet, {'ip': 'rabbit_host', 'port': 'rabbit_port'})
    signals.connect(admin_user, cinder_puppet, {'user_name': 'keystone_user', 'user_password': 'keystone_password', 'tenant_name': 'keystone_tenant'}) #?
    signals.connect(openstack_vhost, cinder_puppet, {'vhost_name': 'rabbit_virtual_host'})
    signals.connect(openstack_rabbitmq_user, cinder_puppet, {'user_name': 'rabbit_userid', 'password': 'rabbit_password'})
    signals.connect(mariadb_service1, cinder_db, {
        'port': 'login_port',
        'root_password': 'login_password',
        'root_user': 'login_user',
        'ip' : 'db_host'})
    signals.connect(mariadb_service1, cinder_db_user, {'port': 'login_port', 'root_password': 'login_password'})
    signals.connect(cinder_db, cinder_db_user, {'db_name', 'db_host'})
    signals.connect(cinder_db_user, cinder_puppet, {
        'user_name':'db_user',
        'db_name':'db_name',
        'user_password':'db_password',
        'db_host' : 'db_host'})
    signals.connect(keystone_puppet, cinder_puppet, {'ip': 'keystone_host', 'admin_port': 'keystone_port'}) #or non admin port?
    signals.connect(services_tenant, cinder_keystone_user)
    signals.connect(cinder_keystone_user, cinder_keystone_role)
    signals.connect(cinder_keystone_user, cinder_puppet, {'user_name': 'keystone_user', 'tenant_name': 'keystone_tenant', 'user_password': 'keystone_password'})
    signals.connect(mariadb_service1, cinder_puppet, {'ip':'ip'})
    signals.connect(cinder_puppet, cinder_keystone_service_endpoint, {
        'ssh_key': 'ssh_key', 'ssh_user': 'ssh_user',
        'ip': ['ip', 'keystone_host', 'admin_ip', 'internal_ip', 'public_ip'],
        'port': ['admin_port', 'internal_port', 'public_port'],})
    signals.connect(keystone_puppet, cinder_keystone_service_endpoint, {
        'admin_port': 'keystone_admin_port', 'admin_token': 'admin_token'})

    # CINDER GLANCE
    # Deploy chain: cinder_puppet -> cinder_glance -> ( cinder_api, cinder_scheduler, cinder_volume )
    cinder_glance_puppet = vr.create('cinder_glance_puppet', 'resources/cinder_glance_puppet', {})[0]
    signals.connect(node1, cinder_glance_puppet)

    # CINDER API
    cinder_api_puppet = vr.create('cinder_api_puppet', 'resources/cinder_api_puppet', {})[0]
    signals.connect(node1, cinder_api_puppet)
    signals.connect(cinder_puppet, cinder_api_puppet, {
        'keystone_password', 'keystone_tenant', 'keystone_user'})
    signals.connect(cinder_puppet, cinder_api_puppet, {
        'keystone_host': 'keystone_auth_host',
        'keystone_port': 'keystone_auth_port'})
    evapi.add_react(cinder_puppet.name, cinder_api_puppet.name, actions=('update',))
    # CINDER SCHEDULER
    cinder_scheduler_puppet = vr.create('cinder_scheduler_puppet', 'resources/cinder_scheduler_puppet', {})[0]
    signals.connect(node1, cinder_scheduler_puppet)
    signals.connect(cinder_puppet, cinder_scheduler_puppet)
    evapi.add_react(cinder_puppet.name, cinder_scheduler_puppet.name, actions=('update',))
    # CINDER VOLUME
    cinder_volume_puppet = vr.create('cinder_volume_puppet', 'resources/cinder_volume_puppet', {})[0]
    signals.connect(node1, cinder_volume_puppet)
    signals.connect(cinder_puppet, cinder_volume_puppet)
    evapi.add_react(cinder_puppet.name, cinder_volume_puppet.name, actions=('update',))

    # NOVA
    nova_puppet = vr.create('nova_puppet', 'resources/nova_puppet', {})[0]
    nova_db = vr.create('nova_db', 'resources/mariadb_db/', {
        'db_name': 'nova_db',
        'login_user': 'root'})[0]
    nova_db_user = vr.create('nova_db_user', 'resources/mariadb_user/', {
        'user_name': 'nova',
        'user_password': 'nova',
        'login_user': 'root'})[0]
    nova_keystone_user = vr.create('nova_keystone_user', 'resources/keystone_user', {
        'user_name': 'nova',
        'user_password': 'nova'})[0]
    nova_keystone_role = vr.create('nova_keystone_role', 'resources/keystone_role', {
        'role_name': 'admin'})[0]
    nova_keystone_service_endpoint = vr.create('nova_keystone_service_endpoint', 'resources/keystone_service_endpoint', {
        'endpoint_name': 'nova',
        'adminurl': 'http://{{admin_ip}}:{{admin_port}}/v2/%(tenant_id)s',
        'internalurl': 'http://{{internal_ip}}:{{internal_port}}/v2/%(tenant_id)s',
        'publicurl': 'http://{{public_ip}}:{{public_port}}/v2/%(tenant_id)s',
        'description': 'OpenStack Compute Service',
        'type': 'compute'})[0]

    signals.connect(node1, nova_puppet)
    signals.connect(node1, nova_db)
    signals.connect(node1, nova_db_user)
    signals.connect(mariadb_service1, nova_db, {
        'port': 'login_port',
        'root_password': 'login_password',
        'root_user': 'login_user',
        'ip' : 'db_host'})
    signals.connect(mariadb_service1, nova_db_user, {
        'port': 'login_port',
        'root_password': 'login_password'})
    signals.connect(admin_user, nova_puppet, {'user_name': 'keystone_user', 'user_password': 'keystone_password', 'tenant_name': 'keystone_tenant'}) #?
    signals.connect(openstack_vhost, nova_puppet, {'vhost_name': 'rabbit_virtual_host'})
    signals.connect(nova_db, nova_db_user, {'db_name', 'db_host'})
    signals.connect(services_tenant, nova_keystone_user)
    signals.connect(nova_keystone_user, nova_keystone_role)
    signals.connect(keystone_puppet, nova_puppet, {
        'ip': 'keystone_host',
        'admin_port': 'keystone_port'})
    signals.connect(nova_keystone_user, nova_puppet, {
        'user_name': 'keystone_user',
        'tenant_name': 'keystone_tenant',
        'user_password': 'keystone_password'})
    signals.connect(rabbitmq_service1, nova_puppet, {
        'ip': 'rabbit_host', 'port': 'rabbit_port'})
    signals.connect(openstack_rabbitmq_user, nova_puppet, {
        'user_name': 'rabbit_userid',
        'password': 'rabbit_password'})
    signals.connect(keystone_puppet, nova_keystone_service_endpoint, {
        'ip': 'keystone_host',
        'admin_port': 'keystone_admin_port',
        'admin_token': 'admin_token'})
    signals.connect(mariadb_service1, nova_puppet, {
        'ip':'db_host'})
    signals.connect(nova_db_user, nova_puppet, {
        'user_name':'db_user',
        'db_name':'db_name',
        'user_password':'db_password',
        'db_host' : 'db_host'})
    signals.connect(nova_puppet, nova_keystone_service_endpoint, {
        'ip': ['ip', 'keystone_host', 'public_ip', 'internal_ip', 'admin_ip'],
        'port': ['admin_port', 'internal_port', 'public_port'],
        'ssh_key': 'ssh_key',
        'ssh_user': 'ssh_user'})

    # NOVA API
    nova_api_puppet = vr.create('nova_api_puppet', 'resources/nova_api_puppet', {})[0]
    signals.connect(node1, nova_api_puppet)
    signals.connect(nova_puppet, nova_api_puppet, {
        'keystone_tenant': 'admin_tenant_name',
        'keystone_user': 'admin_user',
        'keystone_password': 'admin_password',
        'keystone_host': 'auth_host',
        'keystone_port': 'auth_port'})
    signals.connect(nova_api_puppet, neutron_agents_metadata, {'ip': 'metadata_ip'})

    # NOVA CONDUCTOR
    nova_conductor_puppet = vr.create('nova_conductor_puppet', 'resources/nova_conductor_puppet', {})[0]
    signals.connect(node1, nova_conductor_puppet)
    signals.connect(nova_puppet, nova_conductor_puppet)

    # NOVA SCHEDULER
    # NOTE(bogdando) Generic service is used. Package and service names for Ubuntu case
    #   come from https://github.com/openstack/puppet-nova/blob/5.1.0/manifests/params.pp
    nova_scheduler_puppet = vr.create('nova_scheduler_puppet', 'resources/nova_generic_service_puppet', {
        'title' : 'scheduler', 'package_name': 'nova-scheduler', 'service_name': 'nova-scheduler',
    })[0]
    signals.connect(node1, nova_scheduler_puppet)

    # NOVA COMPUTE
    # Deploy chain (nova, node_networking(TODO)) -> (nova_compute_libvirt, nova_neutron) -> nova_compute
    nova_compute_puppet = vr.create('nova_compute_puppet', 'resources/nova_compute_puppet', {})[0]
    # TODO (bogdando) figure out how to use it for multiple glance api servers
    nova_puppet2 = vr.create('nova_puppet2', 'resources/nova_puppet', {
        'glance_api_servers': '{{glance_api_servers_host}}:{{glance_api_servers_port}}'
        })[0]
    signals.connect(nova_puppet, nova_puppet2, {
        'ensure_package', 'rabbit_host',
        'rabbit_password', 'rabbit_port', 'rabbit_userid',
        'rabbit_virtual_host', 'db_user', 'db_password',
        'db_name', 'db_host', 'keystone_password',
        'keystone_port', 'keystone_host', 'keystone_tenant',
        'keystone_user',
    })
    # TODO(bogdando): Make a connection for nova_puppet2.glance_api_servers = "glance_api_puppet.ip:glance_api_puppet.bind_port"
    signals.connect(node2, nova_puppet2)
    signals.connect(node2, nova_compute_puppet)

    # NOVA COMPUTE LIBVIRT, NOVA_NEUTRON
    # NOTE(bogdando): changes nova config, so should notify nova compute service
    nova_compute_libvirt_puppet = vr.create('nova_compute_libvirt_puppet', 'resources/nova_compute_libvirt_puppet', {})[0]
    signals.connect(node2, nova_compute_libvirt_puppet)
    # compute configuration for neutron, use http auth/endpoint protocols, keystone v2 auth hardcoded for the resource
    nova_neutron_puppet = vr.create('nova_neutron_puppet', 'resources/nova_neutron_puppet', {})[0]
    signals.connect(node2, nova_neutron_puppet)
    signals.connect(neutron_server_puppet, nova_neutron_puppet, {
        'auth_password': 'neutron_admin_password',
        'auth_user': 'neutron_admin_username',
        'auth_type': 'neutron_auth_strategy',
        'auth_host': 'auth_host', 'auth_port': 'auth_port',
        'auth_protocol': 'auth_protocol',
    })
    signals.connect(neutron_keystone_service_endpoint, nova_neutron_puppet, {
        'internal_ip':'neutron_endpoint_host',
        'internal_port':'neutron_endpoint_port',
    })

    # signals.connect(keystone_puppet, nova_network_puppet, {'ip': 'keystone_host', 'port': 'keystone_port'})
    # signals.connect(keystone_puppet, nova_keystone_service_endpoint, {'ip': 'keystone_host', 'admin_port': 'keystone_port', 'admin_token': 'admin_token'})
    # signals.connect(rabbitmq_service1, nova_network_puppet, {'ip': 'rabbitmq_host', 'port': 'rabbitmq_port'})

    # GLANCE (base and API)
    glance_api_puppet = vr.create('glance_api_puppet', 'resources/glance_puppet', {})[0]
    glance_db_user = vr.create('glance_db_user', 'resources/mariadb_user/', {
        'user_name': 'glance', 'user_password': 'glance', 'login_user': 'root'})[0]
    glance_db = vr.create('glance_db', 'resources/mariadb_db/', {
        'db_name': 'glance', 'login_user': 'root'})[0]
    glance_keystone_user = vr.create('glance_keystone_user', 'resources/keystone_user', {
        'user_name': 'glance', 'user_password': 'glance123'})[0]
    glance_keystone_role = vr.create('glance_keystone_role', 'resources/keystone_role', {
        'role_name': 'admin'})[0]
    glance_keystone_service_endpoint = vr.create(
        'glance_keystone_service_endpoint',
        'resources/keystone_service_endpoint', {
            'endpoint_name': 'glance',
            'adminurl': 'http://{{admin_ip}}:{{admin_port}}',
            'internalurl': 'http://{{internal_ip}}:{{internal_port}}',
            'publicurl': 'http://{{public_ip}}:{{public_port}}',
            'description': 'OpenStack Image Service', 'type': 'image'})[0]

    signals.connect(node1, glance_api_puppet)
    signals.connect(node1, glance_db)
    signals.connect(node1, glance_db_user)
    signals.connect(admin_user, glance_api_puppet, {
        'user_name': 'keystone_user', 'user_password': 'keystone_password',
        'tenant_name': 'keystone_tenant'}) #?
    signals.connect(mariadb_service1, glance_db, {
        'port': 'login_port',
        'root_password': 'login_password',
        'root_user': 'login_user',
        'ip' : 'db_host'})
    signals.connect(mariadb_service1, glance_db_user, {'port': 'login_port', 'root_password': 'login_password'})
    signals.connect(glance_db, glance_db_user, {'db_name', 'db_host'})
    signals.connect(glance_db_user, glance_api_puppet, {
        'user_name':'db_user',
        'db_name':'db_name',
        'user_password':'db_password',
        'db_host' : 'db_host'})
    signals.connect(keystone_puppet, glance_api_puppet, {'ip': 'keystone_host', 'admin_port': 'keystone_port'}) #or non admin port?
    signals.connect(services_tenant, glance_keystone_user)
    signals.connect(glance_keystone_user, glance_keystone_role)
    signals.connect(glance_keystone_user, glance_api_puppet, {
        'user_name': 'keystone_user', 'tenant_name': 'keystone_tenant',
        'user_password': 'keystone_password'})
    signals.connect(mariadb_service1, glance_api_puppet, {'ip':'ip'})
    signals.connect(glance_api_puppet, glance_keystone_service_endpoint, {
        'ssh_key': 'ssh_key', 'ssh_user': 'ssh_user',
        'ip': ['ip', 'keystone_host', 'admin_ip', 'internal_ip', 'public_ip'],
        'bind_port': ['admin_port', 'internal_port', 'public_port'],})
    signals.connect(keystone_puppet, glance_keystone_service_endpoint, {
        'admin_port': 'keystone_admin_port', 'admin_token': 'admin_token'})

    # GLANCE REGISTRY
    glance_registry_puppet = vr.create('glance_registry_puppet', 'resources/glance_registry_puppet', {})[0]
    signals.connect(node1, glance_registry_puppet)
    signals.connect(glance_api_puppet, glance_registry_puppet)
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

    # Update glance_api_service for cinder
    signals.connect(glance_api_puppet, cinder_glance_puppet, {
        'ip': 'glance_api_servers_host',
        'bind_port': 'glance_api_servers_port'
    })
    # Update glance_api_service for nova compute
    signals.connect(glance_api_puppet, nova_puppet2, {
        'ip': 'glance_api_servers_host',
        'bind_port': 'glance_api_servers_port'
    })

    if PROFILE:
        pr.disable()
        s = StringIO.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print s.getvalue()
        sys.exit(0)

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


resources_to_run = [
    'rabbitmq_service1',
    'openstack_vhost',
    'openstack_rabbitmq_user',

    'mariadb_service1',

    'keystone_db',
    'keystone_db_user',
    'keystone_puppet',
    'openrc_file',

    'admin_tenant',
    'admin_user',
    'admin_role',

    'keystone_service_endpoint',
    'services_tenant',

    'neutron_db',
    'neutron_db_user',
    'neutron_keystone_user',
    'neutron_keystone_role',
    'neutron_puppet',
    'neutron_keystone_service_endpoint',
    'neutron_plugins_ml2',
    'neutron_server_puppet',
    'neutron_agents_ml2',
    'neutron_agents_dhcp',
    'neutron_agents_l3',
    'neutron_agents_metadata',

    'cinder_db',
    'cinder_db_user',
    'cinder_keystone_user',
    'cinder_keystone_role',
    'cinder_puppet',
    'cinder_keystone_service_endpoint',
    'cinder_glance_puppet',
    'cinder_api_puppet',
    'cinder_scheduler_puppet',
    'cinder_volume_puppet',

    'nova_db',
    'nova_db_user',
    'nova_keystone_user',
    'nova_keystone_role',
    'nova_puppet',
    'nova_keystone_service_endpoint',
    'nova_api_puppet',
    'nova_conductor_puppet',
    'nova_scheduler_puppet',

    'glance_db',
    'glance_db_user',
    'glance_keystone_user',
    'glance_keystone_role',
    'glance_keystone_service_endpoint',
    'glance_api_puppet',
    'glance_registry_puppet',

    'nova_puppet2',
    'nova_compute_libvirt_puppet',
    'nova_neutron_puppet',
    'nova_compute_puppet',

    'neutron_puppet2',
    'neutron_plugins_ml22',
    'neutron_agents_ml22',
]


@click.command()
def deploy():
    setup_resources()

    # run
    resources = resource.load_all()
    resources = {r.name: r for r in resources}

    for name in resources_to_run:
        try:
            actions.resource_action(resources[name], 'run')
        except errors.SolarError as e:
            print 'WARNING: %s' % str(e)
            raise

    time.sleep(10)


@click.command()
def undeploy():
    resources = resource.load_all()
    resources = {r.name: r for r in resources}

    for name in reversed(resources_to_run):
        try:
            actions.resource_action(resources[name], 'remove')
        except errors.SolarError as e:
            print 'WARNING: %s' % str(e)

    db.clear()

    signals.Connections.clear()


main.add_command(deploy)
main.add_command(undeploy)


if __name__ == '__main__':
    main()
