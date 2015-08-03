$resource = hiera($::resource_name)

$port = "${resource['input']['port']['value']}"
$management_port = "${resource['input']['management_port']['value']}"

class { '::rabbitmq':
  service_manage    => true,
  port              => $port,
  management_port   => $management_port,
  delete_guest_user => true,
}
