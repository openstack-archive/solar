# Neutron ML2 plugin puppet resource

# === Parameters

source https://github.com/openstack/puppet-neutron/blob/5.1.0/manifests/plugins/ml2.pp

 ``type_drivers``
   (optional) List of network type driver entrypoints to be loaded
   from the neutron.ml2.type_drivers namespace.
   Could be an array that can have these elements:
   local, flat, vlan, gre, vxlan
   Defaults to ['local', 'flat', 'vlan', 'gre', 'vxlan'].

 ``tenant_network_types``
   (optional) Ordered list of network_types to allocate as tenant networks.
   The value 'local' is only useful for single-box testing
   but provides no connectivity between hosts.
   Should be an array that can have these elements:
   local, flat, vlan, gre, vxlan
   Defaults to ['local', 'flat', 'vlan', 'gre', 'vxlan'].

 ``mechanism_drivers``
   (optional) An ordered list of networking mechanism driver
   entrypoints to be loaded from the neutron.ml2.mechanism_drivers namespace.
   Should be an array that can have these elements:
   logger, test, linuxbridge, openvswitch, hyperv, ncs, arista, cisco_nexus,
   l2population, sriovnicswitch
   Default to ['openvswitch', 'linuxbridge'].

 ``flat_networks``
   (optional) List of physical_network names with which flat networks
   can be created. Use * to allow flat networks with arbitrary
   physical_network names.
   Should be an array.
   Default to *.

 ``network_vlan_ranges``
   (optional) List of <physical_network>:<vlan_min>:<vlan_max> or
   <physical_network> specifying physical_network names
   usable for VLAN provider and tenant networks, as
   well as ranges of VLAN tags on each available for
   allocation to tenant networks.
   Should be an array with vlan_min = 1 & vlan_max = 4094 (IEEE 802.1Q)
   Default to empty.

 ``tunnel_id_ranges``
   (optional) Comma-separated list of <tun_min>:<tun_max> tuples
   enumerating ranges of GRE tunnel IDs that are
   available for tenant network allocation
   Should be an array with tun_max +1 - tun_min > 1000000
   Default to empty.

 ``vxlan_group``
   (optional) Multicast group for VXLAN.
   Multicast group for VXLAN. If unset, disables VXLAN enable sending allocate
   broadcast traffic to this multicast group. When left unconfigured, will
   disable multicast VXLAN mode
   Should be an Multicast IP (v4 or v6) address.
   Default to 'None'.

 ``vni_ranges``
   (optional) Comma-separated list of <vni_min>:<vni_max> tuples
   enumerating ranges of VXLAN VNI IDs that are
   available for tenant network allocation.
   Min value is 0 and Max value is 16777215.
   Default to empty.

 ``enable_security_group``
   (optional) Controls if neutron security group is enabled or not.
   It should be false when you use nova security group.
   Defaults to true.

 ``supported_pci_vendor_devs``
   (optional) Supported PCI vendor devices, defined by
   vendor_id:product_id according to the PCI ID
   Repository. Should be an array of devices.
   Defaults to ['15b3:1004', '8086:10ca'] (Intel & Mellanox SR-IOV capable NICs)

 ``sriov_agent_required``
   (optional) SRIOV neutron agent is required for port binding.
   Only set to true if SRIOV network adapters support VF link state setting
   and if admin state management is desired.
   Defaults to false.
