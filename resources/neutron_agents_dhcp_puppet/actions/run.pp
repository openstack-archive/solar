$resource = hiera($::resource_name)

$ip = $resource['input']['ip']['value']

$package_ensure            = $resource['input']['package_ensure']['value']
$debug                     = $resource['input']['debug']['value']
$state_path                = $resource['input']['state_path']['value']
$resync_interval           = $resource['input']['resync_interval']['value']
$interface_driver          = $resource['input']['interface_driver']['value']
$dhcp_driver               = $resource['input']['dhcp_driver']['value']
$root_helper               = $resource['input']['root_helper']['value']
$use_namespaces            = $resource['input']['use_namespaces']['value']
$dnsmasq_config_file       = $resource['input']['dnsmasq_config_file']['value']
$dhcp_delete_namespaces    = $resource['input']['dhcp_delete_namespaces']['value']
$enable_isolated_metadata  = $resource['input']['enable_isolated_metadata']['value']
$enable_metadata_network   = $resource['input']['enable_metadata_network']['value']

class { 'neutron::agents::dhcp':
  enabled                   => true,
  manage_service            => true,
  package_ensure            => $package_ensure,
  debug                     => $debug,
  state_path                => $state_path,
  resync_interval           => $resync_interval,
  interface_driver          => $interface_driver,
  dhcp_driver               => $dhcp_driver,
  root_helper               => $root_helper,
  use_namespaces            => $use_namespaces,
  dnsmasq_config_file       => $dnsmasq_config_file,
  dhcp_delete_namespaces    => $dhcp_delete_namespaces,
  enable_isolated_metadata  => $enable_isolated_metadata,
  enable_metadata_network   => $enable_metadata_network,
}

include neutron::params

package { 'neutron':
  ensure => $package_ensure,
  name   => $::neutron::params::package_name,
}

# Remove external class dependency
Service <| title == 'neutron-dhcp-service' |> {
  require    => undef
}