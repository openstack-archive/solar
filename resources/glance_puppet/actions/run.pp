$resource = hiera($::resource_name)

$ip = $resource['input']['ip']['value']

$db_host = $resource['input']['db_host']['value']
$db_port = $resource['input']['db_port']['value']
$db_user = $resource['input']['db_user']['value']
$db_password = $resource['input']['db_password']['value']
$db_name = $resource['input']['db_name']['value']

$keystone_host = $resource['input']['keystone_host']['value']
$keystone_port = $resource['input']['keystone_port']['value']
$keystone_user = $resource['input']['keystone_user']['value']
$keystone_password = $resource['input']['keystone_password']['value']
$keystone_role = $resource['input']['keystone_role']['value']
$keystone_tenant = $resource['input']['keystone_tenant']['value']

#user { 'glance':
#  name     => 'glance',
#  ensure   => 'present',
#  home     => '/home/glance',
#  system   => true
#}
#
#class {'glance':
#  package_ensure       => 'present'
#}

class { 'glance::api':
  #package_ensure      => 'present',
  verbose             => true,
  keystone_tenant     => $keystone_tenant,
  keystone_user       => $keystone_user,
  keystone_password   => $keystone_password,
  database_connection => "mysql://$db_user:$db_password@$db_host/$db_name",
}

class { 'glance::registry':
  package_ensure      => 'present',
  verbose             => true,
  keystone_tenant     => $keystone_tenant,
  keystone_user       => $keystone_user,
  keystone_password   => $keystone_password,
  database_connection => "mysql://$db_user:$db_password@$db_host/$db_name",
}

class { 'glance::backend::file': }

#file { '/etc/keystone/keystone-exports':
#  owner     => 'root',
#  group     => 'root',
#  content   => template('keystone/exports.erb')
#}
