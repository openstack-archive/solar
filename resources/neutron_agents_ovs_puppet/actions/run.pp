$resource = hiera($::resource_name)

$ip = $resource['input']['ip']['value']

$package_ensure      = $resource['input']['package_ensure']['value']
$bridge_uplinks      = $resource['input']['bridge_uplinks']['value']
$bridge_mappings     = $resource['input']['bridge_mappings']['value']
$integration_bridge  = $resource['input']['integration_bridge']['value']
$enable_tunneling    = $resource['input']['enable_tunneling']['value']
$tunnel_types        = $resource['input']['tunnel_types']['value']
$local_ip            = $resource['input']['local_ip']['value']
$tunnel_bridge       = $resource['input']['tunnel_bridge']['value']
$vxlan_udp_port      = $resource['input']['vxlan_udp_port']['value']
$polling_interval    = $resource['input']['polling_interval']['value']
$firewall_driver     = $resource['input']['firewall_driver']['value']
$veth_mtu            = $resource['input']['veth_mtu']['value']

class { 'neutron::agents::ovs':
  enabled             => true,
  manage_service      => true,
  package_ensure      => $package_ensure,
  bridge_uplinks      => $bridge_uplinks,
  bridge_mappings     => $bridge_mappings,
  integration_bridge  => $integration_bridge,
  enable_tunneling    => $enable_tunneling,
  tunnel_types        => $tunnel_types,
  local_ip            => $local_ip,
  tunnel_bridge       => $tunnel_bridge,
  vxlan_udp_port      => $vxlan_udp_port,
  polling_interval    => $polling_interval,
  firewall_driver     => $firewall_driver,
  veth_mtu            => $veth_mtu,
}

# Remove external class dependency
Service <| title == 'neutron-plugin-ovs-service' |> {
  require    => undef
}