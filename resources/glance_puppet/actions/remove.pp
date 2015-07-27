$resource = hiera($::resource_name)

class {'glance::api':
  enabled                   => false,
}

class {'glance':
  package_ensure       => 'absent'
}
