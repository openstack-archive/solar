$resource = hiera('{{ resource_name }}')

$rabbitmq_user = $resource['input']['rabbitmq_user']['value']
$rabbitmq_password = $resource['input']['rabbitmq_password']['value']
$rabbitmq_host = $resource['input']['rabbitmq_host']['value']
$rabbitmq_port = $resource['input']['rabbitmq_port']['value']

class { 'neutron::server':
  enabled          => false,
  package_ensure   => 'absent',
  auth_type        => 'noauth'
}

class { 'neutron':
  enabled        => false,
  package_ensure => 'absent',
  rabbit_user     => $rabbitmq_user,
  rabbit_password => $rabbitmq_password,
  rabbit_host     => $rabbitmq_host,
  rabbit_port     => $rabbitmq_port
}

