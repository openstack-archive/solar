$resource = hiera($::resource_name)

$ip = $resource['input']['ip']['value']

#class {'glance':
#  package_ensure       => 'absent'
#}
#
#user { 'glance':
#  name     => 'glance',
#  ensure   => 'absent',
#  home     => '/home/glance',
#  system   => true
#}


class { 'glance::api':
  #package_ensure      => 'absent',
  verbose             => true
}

class { 'glance::registry':
  package_ensure      => 'absent',
  verbose             => true
}

class { 'glance::backend::file': }
