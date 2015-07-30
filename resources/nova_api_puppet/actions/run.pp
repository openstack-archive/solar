$resource = hiera($::resource_name)

$ensure_package                        = $resource['input']['ensure_package']['value']
$auth_strategy                         = $resource['input']['auth_strategy']['value']
$auth_host                             = $resource['input']['auth_host']['value']
$auth_port                             = $resource['input']['auth_port']['value']
$auth_protocol                         = $resource['input']['auth_protocol']['value']
$auth_uri                              = $resource['input']['auth_uri']['value']
$auth_admin_prefix                     = $resource['input']['auth_admin_prefix']['value']
$auth_version                          = $resource['input']['auth_version']['value']
$admin_tenant_name                     = $resource['input']['admin_tenant_name']['value']
$admin_user                            = $resource['input']['admin_user']['value']
$admin_password                        = $resource['input']['admin_password']['value']
$api_bind_address                      = $resource['input']['api_bind_address']['value']
$metadata_listen                       = $resource['input']['metadata_listen']['value']
$enabled_apis                          = $resource['input']['enabled_apis']['value']
$keystone_ec2_url                      = $resource['input']['keystone_ec2_url']['value']
$volume_api_class                      = $resource['input']['volume_api_class']['value']
$use_forwarded_for                     = $resource['input']['use_forwarded_for']['value']
$osapi_compute_workers                 = $resource['input']['osapi_compute_workers']['value']
$ec2_workers                           = $resource['input']['ec2_workers']['value']
$metadata_workers                      = $resource['input']['metadata_workers']['value']
$sync_db                               = $resource['input']['sync_db']['value']
$neutron_metadata_proxy_shared_secret  = $resource['input']['neutron_metadata_proxy_shared_secret']['value']
$osapi_v3                              = $resource['input']['osapi_v3']['value']
$pci_alias                             = $resource['input']['pci_alias']['value']
$ratelimits                            = $resource['input']['ratelimits']['value']
$ratelimits_factory                    = $resource['input']['ratelimits_factory']['value']
$validate                              = $resource['input']['validate']['value']
$validation_options                    = $resource['input']['validation_options']['value']
$workers                               = $resource['input']['workers']['value']
$conductor_workers                     = $resource['input']['conductor_workers']['value']

exec { 'post-nova_config':
  command     => '/bin/echo "Nova config has changed"',
}

include nova::params

package { 'nova-common':
  name   => $nova::params::common_package_name,
  ensure => $ensure_package,
}

class { 'nova::api':
  enabled                               => true,
  manage_service                        => true,
  ensure_package                        => $ensure_package,
  auth_strategy                         => $auth_strategy,
  auth_host                             => $auth_host,
  auth_port                             => $auth_port,
  auth_protocol                         => $auth_protocol,
  auth_uri                              => $auth_uri,
  auth_admin_prefix                     => $auth_admin_prefix,
  auth_version                          => $auth_version,
  admin_tenant_name                     => $admin_tenant_name,
  admin_user                            => $admin_user,
  admin_password                        => $admin_password,
  api_bind_address                      => $api_bind_address,
  metadata_listen                       => $metadata_listen,
  enabled_apis                          => $enabled_apis,
  keystone_ec2_url                      => $keystone_ec2_url,
  volume_api_class                      => $volume_api_class,
  use_forwarded_for                     => $use_forwarded_for,
  osapi_compute_workers                 => $osapi_compute_workers,
  ec2_workers                           => $ec2_workers,
  metadata_workers                      => $metadata_workers,
  sync_db                               => $sync_db,
  neutron_metadata_proxy_shared_secret  => $neutron_metadata_proxy_shared_secret,
  osapi_v3                              => $osapi_v3,
  pci_alias                             => $pci_alias,
  ratelimits                            => $ratelimits,
  ratelimits_factory                    => $ratelimits_factory,
  validate                              => $validate,
  validation_options                    => $validation_options,
  workers                               => $workers,
  conductor_workers                     => $conductor_workers,
}
