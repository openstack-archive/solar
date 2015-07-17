$resource = hiera($::resource_name)

$rabbitmq_user = $resource['input']['rabbitmq_user']['value']
$rabbitmq_password = $resource['input']['rabbitmq_password']['value']
$rabbitmq_host = $resource['input']['rabbitmq_host']['value']
$db_user = $resource['input']['db_user']['value']
$db_password = $resource['input']['db_password']['value']
$db_name = $resource['input']['db_name']['value']
$db_host = $resource['input']['db_host']['value']
$keystone_password = $resource['input']['keystone_password']['value']
$keystone_host = $resource['input']['keystone_host']['value']
$keystone_port =  $resource['input']['keystone_port']['value']
$keystone_tenant_name = $resource['input']['keystone_tenant_name']['value']
$keystone_user = $resource['input']['keystone_user_name']['value']

class { 'nova':
  database_connection => "mysql://${db_user}:${db_password}@${db_host}/${db_name}?charset=utf8",
  rabbit_userid       => $rabbitmq_user,
  rabbit_password     => $rabbitmq_password,
  rabbit_host         => $rabbitmq_host,
  image_service       => 'nova.image.glance.GlanceImageService',
  glance_api_servers  => 'localhost:9292',
  verbose             => false,
}

class { 'nova::api':
  enabled            => true,
  admin_user         => $keystone_user,
  admin_password     => $keystone_password,
  auth_host          => $keystone_host,
  auth_port          => $keystone_port,
  admin_tenant_name  => $keystone_tenant_name,
}
