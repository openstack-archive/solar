$resource = hiera('{{ resource_name }}')

$port = "${resource['input']['port']['value']}"
$management_port = "${resource['input']['management_port']['value']}"
$node_name = $resource['input']['node_name']['value']

class { '::rabbitmq':
  service_manage    => false,
  port              => $port,
  management_port   => $management_port,
  delete_guest_user => true,
  environment_variables   => {
    'RABBITMQ_NODENAME'     => $node_name,
    'RABBITMQ_SERVICENAME'  => 'RabbitMQ'
  }
}
