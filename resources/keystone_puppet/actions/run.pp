$resource = hiera('{{ name }}')
$ip = $resource['input']['ip']['value']
$admin_token = $resource['input']['admin_token']['value']
$db_user = $resource['input']['db_user']['value']
$db_password = $resource['input']['db_password']['value']
$db_name = $resource['input']['db_name']['value']
$port = $resource['input']['port']['value']

class {'keystone':
  verbose         => True,
  catalog_type    => 'sql',
  admin_token     => $admin_token,
  sql_connection  => "mysql://$db_user:$db_password@$ip/$db_name",
  public_port     => "$port"
}