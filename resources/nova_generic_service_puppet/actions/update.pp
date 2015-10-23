$resource = hiera($::resource_name)

$service_title           = $resource['input']['title']['value']
$package_name    = $resource['input']['package_name']['value']
$service_name    = $resource['input']['service_name']['value']
$ensure_package  = $resource['input']['ensure_package']['value']

exec { 'post-nova_config':
  command     => '/bin/echo "Nova config has changed"',
}

include nova::params

package { 'nova-common':
  name   => $nova::params::common_package_name,
  ensure => $ensure_package,
}

nova::generic_service { $service_title:
  enabled         => true,
  manage_service  => true,
  package_name    => $package_name,
  service_name    => $service_name,
  ensure_package  => $ensure_package,
}

notify { "restart generic service":
  notify => Service["nova-${service_title}"],
}
