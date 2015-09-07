$service_title           = $resource['input']['title']['value']
$package_name    = $resource['input']['package_name']['value']
$service_name    = $resource['input']['service_name']['value']

exec { 'post-nova_config':
  command     => '/bin/echo "Nova config has changed"',
}

nova::generic_service { $service_title:
  ensure_package => 'absent',
  enabled        => false,
  package_name   => $package_name,
  service_name   => $service_name,
}

include nova::params

package { 'nova-common':
  name   => $nova::params::common_package_name,
  ensure => 'absent',
}