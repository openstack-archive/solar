# Neutron DHCP agent puppet resource

Setups Neutron DHCP agent.

# Parameters

https://github.com/openstack/puppet-neutron/blob/5.1.0/manifests/agents/dhcp.pp


 ``package_ensure``
   (optional) Ensure state for package. Defaults to 'present'.

 ``debug``
   (optional) Show debugging output in log. Defaults to false.

 ``state_path``
   (optional) Where to store dnsmasq state files. This directory must be
   writable by the user executing the agent. Defaults to '/var/lib/neutron'.

 ``resync_interval``
   (optional) The DHCP agent will resync its state with Neutron to recover
   from any transient notification or rpc errors. The interval is number of
   seconds between attempts. Defaults to 30.

 ``interface_driver``
   (optional) Defaults to 'neutron.agent.linux.interface.OVSInterfaceDriver'.

 ``dhcp_driver``
   (optional) Defaults to 'neutron.agent.linux.dhcp.Dnsmasq'.

 ``root_helper``
   (optional) Defaults to 'sudo neutron-rootwrap /etc/neutron/rootwrap.conf'.
   Addresses bug: https://bugs.launchpad.net/neutron/+bug/1182616
   Note: This can safely be removed once the module only targets the Havana release.

 ``use_namespaces``
   (optional) Allow overlapping IP (Must have kernel build with
   CONFIG_NET_NS=y and iproute2 package that supports namespaces).
   Defaults to true.

 ``dnsmasq_config_file``
   (optional) Override the default dnsmasq settings with this file.
   Defaults to undef

 ``dhcp_delete_namespaces``
   (optional) Delete namespace after removing a dhcp server
   Defaults to false.

 ``enable_isolated_metadata``
   (optional) enable metadata support on isolated networks.
   Defaults to false.

 ``enable_metadata_network``
   (optional) Allows for serving metadata requests coming from a dedicated metadata
   access network whose cidr is 169.254.169.254/16 (or larger prefix), and is
   connected to a Neutron router from which the VMs send metadata request.
   This option requires enable_isolated_metadata = True
   Defaults to false.