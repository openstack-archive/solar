$resource = hiera($::resource_name)

$ip = $resource['input']['ip']['value']

$rabbitmq_user = $resource['input']['rabbitmq_user']['value']
$rabbitmq_password = $resource['input']['rabbitmq_password']['value']
$rabbitmq_host = $resource['input']['rabbitmq_host']['value']
$rabbitmq_port = $resource['input']['rabbitmq_port']['value']
$rabbitmq_virtual_host = $resource['input']['rabbitmq_virtual_host']['value']

$keystone_host = $resource['input']['keystone_host']['value']
$keystone_port = $resource['input']['keystone_port']['value']
$keystone_user = $resource['input']['keystone_user']['value']
$keystone_password = $resource['input']['keystone_password']['value']
$keystone_tenant = $resource['input']['keystone_tenant']['value']

class { 'neutron':
  debug           => true,
  verbose         => true,
  enabled         => true,
  package_ensure  => 'present',
  auth_strategy   => 'keystone',
  rabbit_user     => $rabbitmq_user,
  rabbit_password => $rabbitmq_password,
  rabbit_host     => $rabbitmq_host,
  rabbit_port     => $rabbitmq_port,
  rabbit_virtual_host => $rabbitmq_virtual_host,
  service_plugins => ['metering']
}

class { 'neutron::server':
  enabled          => true,
  package_ensure   => 'present',
  auth_type        => 'keystone',
  auth_password    => $keystone_password,
  auth_user        => $keystone_user,
  auth_tenant      => $keystone_tenant
}

class { 'neutron::agents::dhcp': }

#file { '/etc/neutron/neutron-exports':
#  owner     => 'root',
#  group     => 'root',
#  content   => template('neutron/exports.erb')
#}
