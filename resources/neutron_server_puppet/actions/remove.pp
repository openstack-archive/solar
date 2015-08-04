class { 'neutron::server':
  enabled         => false,
  package_ensure  => 'absent',
  auth_password   => 'not important as removed',
}