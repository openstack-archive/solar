$resource = hiera($::resource_name)

$ip = $resource['input']['ip']['value']

$package_ensure              = $resource['input']['package_ensure']['value']
$enabled                     = $resource['input']['enabled']['value']
$bridge_uplinks              = $resource['input']['bridge_uplinks']['value']
$bridge_mappings             = $resource['input']['bridge_mappings']['value']
$integration_bridge          = $resource['input']['integration_bridge']['value']
$enable_tunneling            = $resource['input']['enable_tunneling']['value']
$tunnel_types                = $resource['input']['tunnel_types']['value']
$local_ip                    = $resource['input']['local_ip']['value']
$tunnel_bridge               = $resource['input']['tunnel_bridge']['value']
$vxlan_udp_port              = $resource['input']['vxlan_udp_port']['value']
$polling_interval            = $resource['input']['polling_interval']['value']
$l2_population               = $resource['input']['l2_population']['value']
$arp_responder               = $resource['input']['arp_responder']['value']
$firewall_driver             = $resource['input']['firewall_driver']['value']
$enable_distributed_routing  = $resource['input']['enable_distributed_routing']['value']

class { 'neutron::agents::ml2::ovs':
  enabled                     => true,
  package_ensure              => $package_ensure,
  bridge_uplinks              => $bridge_uplinks,
  bridge_mappings             => $bridge_mappings,
  integration_bridge          => $integration_bridge,
  enable_tunneling            => $enable_tunneling,
  tunnel_types                => $tunnel_types,
  local_ip                    => $local_ip,
  tunnel_bridge               => $tunnel_bridge,
  vxlan_udp_port              => $vxlan_udp_port,
  polling_interval            => $polling_interval,
  l2_population               => $l2_population,
  arp_responder               => $arp_responder,
  firewall_driver             => $firewall_driver,
  enable_distributed_routing  => $enable_distributed_routing,
}

# Remove external class dependency and restore required ones
Service <| title == 'neutron-ovs-agent-service' |> {
  require    => undef
}
Neutron_plugin_ml2<||> ~> Service['neutron-ovs-agent-service']
File['/etc/neutron/plugins/openvswitch/ovs_neutron_plugin.ini'] ~>
Service<| title == 'neutron-ovs-agent-service' |>