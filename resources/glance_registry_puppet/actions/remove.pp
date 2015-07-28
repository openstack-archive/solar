$resource = hiera($::resource_name)

class {'glance::registry':
  enabled        => false,
  package_ensure => 'absent',
}
