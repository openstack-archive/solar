# Neutron OVS agent with ML2 plugin puppet resource

Setups OVS neutron agent when using ML2 plugin

# === Parameters

source https://github.com/openstack/puppet-neutron/blob/5.1.0/manifests/agents/ml2/ovs.pp

 ``package_ensure``
   (optional) The state of the package
   Defaults to 'present'

 ``enabled``
   (required) Whether or not to enable the OVS Agent
   Defaults to true

 ``bridge_uplinks``
   (optional) List of interfaces to connect to the bridge when doing
   bridge mapping.
   Defaults to empty list

 ``bridge_mapping``
   (optional) List of <physical_network>:<bridge>
   Defaults to empty list

 ``integration_bridge``
   (optional) Integration bridge in OVS
   Defaults to 'br-int'

 ``enable_tunneling``
   (optional) Enable or not tunneling
   Defaults to false

 ``tunnel_types``
   (optional) List of types of tunnels to use when utilizing tunnels,
   either 'gre' or 'vxlan'.
   Defaults to false

 ``local_ip``
   (optional) Local IP address of GRE tunnel endpoints.
   Required when enabling tunneling
   Defaults to false

 ``tunnel_bridge``
   (optional) Bridge used to transport tunnels
   Defaults to 'br-tun'

 ``vxlan_udp_port``
   (optional) The UDP port to use for VXLAN tunnels.
   Defaults to '4789'

 ``polling_interval``
   (optional) The number of seconds the agent will wait between
   polling for local device changes.
   Defaults to '2"

 ``l2_population``
   (optional) Extension to use alongside ml2 plugin's l2population
   mechanism driver.
   Defaults to false

 ``arp_responder``
   (optional) Enable or not the ARP responder.
   Recommanded when using l2 population mechanism driver.
   Defaults to false

 ``firewall_driver``
   (optional) Firewall driver for realizing neutron security group function.
   Defaults to 'neutron.agent.linux.iptables_firewall.OVSHybridIptablesFirewallDriver'.

 ``enable_distributed_routing``
   (optional) Set to True on L2 agents to enable support
   for distributed virtual routing.
   Defaults to false