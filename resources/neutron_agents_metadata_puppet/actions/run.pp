$resource = hiera($::resource_name)

$ip = $resource['input']['ip']['value']

$auth_host          = $resource['input']['auth_host']['value']
$auth_port          = $resource['input']['auth_port']['value']

$auth_password              = $resource['input']['auth_password']['value']
$shared_secret              = $resource['input']['shared_secret']['value']
$package_ensure             = $resource['input']['package_ensure']['value']
$debug                      = $resource['input']['debug']['value']
$auth_tenant                = $resource['input']['auth_tenant']['value']
$auth_user                  = $resource['input']['auth_user']['value']
$auth_insecure              = $resource['input']['auth_insecure']['value']
$auth_ca_cert               = $resource['input']['auth_ca_cert']['value']
$auth_region                = $resource['input']['auth_region']['value']
$metadata_ip                = $resource['input']['metadata_ip']['value']
$metadata_port              = $resource['input']['metadata_port']['value']
$metadata_workers           = $resource['input']['metadata_workers']['value']
$metadata_backlog           = $resource['input']['metadata_backlog']['value']
$metadata_memory_cache_ttl  = $resource['input']['metadata_memory_cache_ttl']['value']

class { 'neutron::agents::metadata':
  enabled                    => true,
  manage_service             => true,
  auth_password              => $auth_password,
  shared_secret              => $shared_secret,
  package_ensure             => $package_ensure,
  debug                      => $debug,
  auth_tenant                => $auth_tenant,
  auth_user                  => $auth_user,
  auth_url                   => "http://${auth_host}:${auth_port}/v2.0",
  auth_insecure              => $auth_insecure,
  auth_ca_cert               => $auth_ca_cert,
  auth_region                => $auth_region,
  metadata_ip                => $metadata_ip,
  metadata_port              => $metadata_port,
  metadata_workers           => $metadata_workers,
  metadata_backlog           => $metadata_backlog,
  metadata_memory_cache_ttl  => $metadata_memory_cache_ttl,
}

include neutron::params

package { 'neutron':
  ensure => $package_ensure,
  name   => $::neutron::params::package_name,
}

# Remove external class dependency
Service <| title == 'neutron-metadata' |> {
  require    => undef
}