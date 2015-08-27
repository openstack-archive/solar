class { 'neutron::plugins::ovs':
  package_ensure    => 'absent',
}

include neutron::params

package { 'neutron':
  ensure => 'absent',
  name   => $::neutron::params::package_name,
}

# Remove external class dependency
Service <| title == 'neutron-plugin-ovs-service' |> {
  require    => undef
}