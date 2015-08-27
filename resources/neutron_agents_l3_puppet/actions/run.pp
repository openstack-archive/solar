$resource = hiera($::resource_name)

$ip = $resource['input']['ip']['value']

$package_ensure                    = $resource['input']['package_ensure']['value']
$debug                             = $resource['input']['debug']['value']
$external_network_bridge           = $resource['input']['external_network_bridge']['value']
$use_namespaces                    = $resource['input']['use_namespaces']['value']
$interface_driver                  = $resource['input']['interface_driver']['value']
$router_id                         = $resource['input']['router_id']['value']
$gateway_external_network_id       = $resource['input']['gateway_external_network_id']['value']
$handle_internal_only_routers      = $resource['input']['handle_internal_only_routers']['value']
$metadata_port                     = $resource['input']['metadata_port']['value']
$send_arp_for_ha                   = $resource['input']['send_arp_for_ha']['value']
$periodic_interval                 = $resource['input']['periodic_interval']['value']
$periodic_fuzzy_delay              = $resource['input']['periodic_fuzzy_delay']['value']
$enable_metadata_proxy             = $resource['input']['enable_metadata_proxy']['value']
$network_device_mtu                = $resource['input']['network_device_mtu']['value']
$router_delete_namespaces          = $resource['input']['router_delete_namespaces']['value']
$ha_enabled                        = $resource['input']['ha_enabled']['value']
$ha_vrrp_auth_type                 = $resource['input']['ha_vrrp_auth_type']['value']
$ha_vrrp_auth_password             = $resource['input']['ha_vrrp_auth_password']['value']
$ha_vrrp_advert_int                = $resource['input']['ha_vrrp_advert_int']['value']
$agent_mode                        = $resource['input']['agent_mode']['value']
$allow_automatic_l3agent_failover  = $resource['input']['allow_automatic_l3agent_failover']['value']

class { 'neutron::agents::l3':
  enabled                           => true,
  manage_service                    => true,
  package_ensure                    => $package_ensure,
  debug                             => $debug,
  external_network_bridge           => $external_network_bridge,
  use_namespaces                    => $use_namespaces,
  interface_driver                  => $interface_driver,
  router_id                         => $router_id,
  gateway_external_network_id       => $gateway_external_network_id,
  handle_internal_only_routers      => $handle_internal_only_routers,
  metadata_port                     => $metadata_port,
  send_arp_for_ha                   => $send_arp_for_ha,
  periodic_interval                 => $periodic_interval,
  periodic_fuzzy_delay              => $periodic_fuzzy_delay,
  enable_metadata_proxy             => $enable_metadata_proxy,
  network_device_mtu                => $network_device_mtu,
  router_delete_namespaces          => $router_delete_namespaces,
  ha_enabled                        => $ha_enabled,
  ha_vrrp_auth_type                 => $ha_vrrp_auth_type,
  ha_vrrp_auth_password             => $ha_vrrp_auth_password,
  ha_vrrp_advert_int                => $ha_vrrp_advert_int,
  agent_mode                        => $agent_mode,
  allow_automatic_l3agent_failover  => $allow_automatic_l3agent_failover,
}

include neutron::params

package { 'neutron':
  ensure => $package_ensure,
  name   => $::neutron::params::package_name,
}

# Remove external class dependency
Service <| title == 'neutron-l3' |> {
  require    => undef
}