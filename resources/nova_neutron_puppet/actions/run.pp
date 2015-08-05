$resource = hiera($::resource_name)

$libvirt_vif_driver               = $resource['input']['libvirt_vif_driver']['value']
$force_snat_range                 = $resource['input']['force_snat_range']['value']
$neutron_admin_password           = $resource['input']['neutron_admin_password']['value']
$neutron_auth_strategy            = $resource['input']['neutron_auth_strategy']['value']
$neutron_url                      = $resource['input']['neutron_url']['value']
$neutron_url_timeout              = $resource['input']['neutron_url_timeout']['value']
$neutron_admin_tenant_name        = $resource['input']['neutron_admin_tenant_name']['value']
$neutron_default_tenant_id        = $resource['input']['neutron_default_tenant_id']['value']
$neutron_region_name              = $resource['input']['neutron_region_name']['value']
$neutron_admin_username           = $resource['input']['neutron_admin_username']['value']
$neutron_admin_auth_url           = $resource['input']['neutron_admin_auth_url']['value']
$neutron_ovs_bridge               = $resource['input']['neutron_ovs_bridge']['value']
$neutron_extension_sync_interval  = $resource['input']['neutron_extension_sync_interval']['value']
$neutron_ca_certificates_file     = $resource['input']['neutron_ca_certificates_file']['value']
$network_api_class                = $resource['input']['network_api_class']['value']
$security_group_api               = $resource['input']['security_group_api']['value']
$firewall_driver                  = $resource['input']['firewall_driver']['value']
$vif_plugging_is_fatal            = $resource['input']['vif_plugging_is_fatal']['value']
$vif_plugging_timeout             = $resource['input']['vif_plugging_timeout']['value']
$dhcp_domain                      = $resource['input']['dhcp_domain']['value']


class { 'nova::compute::neutron':
  libvirt_vif_driver               => $libvirt_vif_driver,
  force_snat_range                 => $force_snat_range,
}

class { 'nova::network::neutron':
  neutron_admin_password           => $neutron_admin_password,
  neutron_auth_strategy            => $neutron_auth_strategy,
  neutron_url                      => $neutron_url,
  neutron_url_timeout              => $neutron_url_timeout,
  neutron_admin_tenant_name        => $neutron_admin_tenant_name,
  neutron_default_tenant_id        => $neutron_default_tenant_id,
  neutron_region_name              => $neutron_region_name,
  neutron_admin_username           => $neutron_admin_username,
  neutron_admin_auth_url           => $neutron_admin_auth_url,
  neutron_ovs_bridge               => $neutron_ovs_bridge,
  neutron_extension_sync_interval  => $neutron_extension_sync_interval,
  neutron_ca_certificates_file     => $neutron_ca_certificates_file,
  network_api_class                => $network_api_class,
  security_group_api               => $security_group_api,
  firewall_driver                  => $firewall_driver,
  vif_plugging_is_fatal            => $vif_plugging_is_fatal,
  vif_plugging_timeout             => $vif_plugging_timeout,
  dhcp_domain                      => $dhcp_domain,
}
