class {'cinder::api':
  enabled            => false,
  package_ensure     => 'absent'
}

include cinder::params

package { 'cinder':
  ensure  => 'absent',
  name    => $::cinder::params::package_name,
}