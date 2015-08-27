# Neutron OVS plugin puppet resource

Configure the neutron server to use the OVS plugin.
This configures the plugin for the API server, but does nothing
about configuring the agents that must also run and share a config
file with the OVS plugin if both are on the same machine.

Note, this plugin was deprecated, you may want to use the ML2 plugin instead.

NB: don't need tunnel ID range when using VLANs,
*but* you do need the network vlan range regardless of type,
because the list of networks there is still important
even if the ranges aren't specified
if type is vlan or flat, a default of physnet1:1000:2000 is used
otherwise this will not be set by default.

source https://github.com/openstack/puppet-neutron/blob/5.1.0/manifests/plugins/ovs.pp