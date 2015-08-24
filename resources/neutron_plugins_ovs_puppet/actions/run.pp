$resource = hiera($::resource_name)

$ip = $resource['input']['ip']['value']

$db_user = $resource['input']['db_user']['value']
$db_host = $resource['input']['db_host']['value']
$db_password = $resource['input']['db_password']['value']
$db_name = $resource['input']['db_name']['value']

$package_ensure       = $resource['input']['package_ensure']['value']
$sql_max_retries      = $resource['input']['sql_max_retries']['value']
$sql_idle_timeout     = $resource['input']['sql_idle_timeout']['value']
$reconnect_interval   = $resource['input']['reconnect_interval']['value']
$tenant_network_type  = $resource['input']['tenant_network_type']['value']
$network_vlan_ranges  = $resource['input']['network_vlan_ranges']['value']
$tunnel_id_ranges     = $resource['input']['tunnel_id_ranges']['value']
$vxlan_udp_port       = $resource['input']['vxlan_udp_port']['value']

# Stamp neutron head, if current version is None, or upgrade head would fail later
$command = '/usr/bin/neutron-db-manage --config-file /etc/neutron/neutron.conf --config-file /etc/neutron/plugin.ini'
class { 'neutron::plugins::ovs':
  package_ensure       => $package_ensure,
  sql_connection       => "mysql://${db_user}:${db_password}@${db_host}/${db_name}",
  sql_max_retries      => $sql_max_retries,
  sql_idle_timeout     => $sql_idle_timeout,
  reconnect_interval   => $reconnect_interval,
  tenant_network_type  => $tenant_network_type,
  network_vlan_ranges  => $network_vlan_ranges,
  tunnel_id_ranges     => $tunnel_id_ranges,
  vxlan_udp_port       => $vxlan_udp_port,
} ->

exec { 'neutron-db-sync':
  provider    => 'shell',
  command     => "${command} stamp head",
  path        => [ '/usr/bin', '/bin' ],
  onlyif      => "${command} current | grep -qE '^Current revision.*None$' "
}

include neutron::params

package { 'neutron':
  ensure => $package_ensure,
  name   => $::neutron::params::package_name,
  before => Exec['neutron-db-sync']
}

# Remove external class dependency
Service <| title == 'neutron-plugin-ovs-service' |> {
  require    => undef
}
