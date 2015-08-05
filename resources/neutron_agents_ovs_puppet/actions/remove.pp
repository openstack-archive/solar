class { 'neutron::agents::ovs':
  package_ensure    => 'absent',
  enabled           => false,
}