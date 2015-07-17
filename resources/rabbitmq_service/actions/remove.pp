$resource = hiera($::resource_name)

$node_name = $resource['input']['node_name']['value']

class { '::rabbitmq':
  package_ensure    => 'absent',
  environment_variables   => {
    'RABBITMQ_NODENAME'     => $node_name,
    'RABBITMQ_SERVICENAME'  => 'RabbitMQ'
  }
}

