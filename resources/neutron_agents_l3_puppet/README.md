# Neutron L3 agent puppet resource

Installs and configures the Neutron L3 service
TODO: create ability to have multiple L3 services

# Parameters

https://github.com/openstack/puppet-neutron/blob/5.1.0/manifests/agents/l3.pp

 ``package_ensure``
   (optional) The state of the package
   Defaults to present

 ``debug``
   (optional) Print debug info in logs
   Defaults to false

 ``external_network_bridge``
   (optional) The name of the external bridge
   Defaults to br-ex

 ``use_namespaces``
   (optional) Enable overlapping IPs / network namespaces
   Defaults to false

 ``interface_driver``
   (optional) Driver to interface with neutron
   Defaults to OVSInterfaceDriver

 ``router_id``
   (optional) The ID of the external router in neutron
   Defaults to blank

 ``gateway_external_network_id``
   (optional) The ID of the external network in neutron
   Defaults to blank

 ``handle_internal_only_routers``
   (optional) L3 Agent will handle non-external routers
   Defaults to true

 ``metadata_port``
   (optional) The port of the metadata server
   Defaults to 9697

 ``send_arp_for_ha``
   (optional) Send this many gratuitous ARPs for HA setup. Set it below or equal to 0
   to disable this feature.
   Defaults to 3

 ``periodic_interval``
   (optional) seconds between re-sync routers' data if needed
   Defaults to 40

 ``periodic_fuzzy_delay``
   (optional) seconds to start to sync routers' data after starting agent
   Defaults to 5

 ``enable_metadata_proxy``
   (optional) can be set to False if the Nova metadata server is not available
   Defaults to True

 ``network_device_mtu``
   (optional) The MTU size for the interfaces managed by the L3 agent
   Defaults to undef
   Should be deprecated in the next major release in favor of a global parameter

 ``router_delete_namespaces``
   (optional) namespaces can be deleted cleanly on the host running the L3 agent
   Defaults to False

 ``ha_enabled``
   (optional) Enabled or not HA for L3 agent.
   Defaults to false

 ``ha_vrrp_auth_type``
   (optional) VRRP authentication type. Can be AH or PASS.
   Defaults to "PASS"

 ``ha_vrrp_auth_password``
   (optional) VRRP authentication password. Required if ha_enabled = true.
   Defaults to undef

 ``ha_vrrp_advert_int``
   (optional) The advertisement interval in seconds.
   Defaults to '2'

 ``agent_mode``
   (optional) The working mode for the agent.
   'legacy': default behavior (without DVR)
   'dvr': enable DVR for an L3 agent running on compute node (DVR in production)
   'dvr_snat': enable DVR with centralized SNAT support (DVR for single-host, for testing only)
   Defaults to 'legacy'

 ``allow_automatic_l3agent_failover``
   (optional) Automatically reschedule routers from offline L3 agents to online
   L3 agents.
   This is another way to run virtual routers in highly available way but with slow
   failover performances compared to Keepalived feature in Neutron L3 Agent.
   Defaults to 'False'