$resource = hiera($::resource_name)

$ip = $resource['input']['ip']['value']

$db_user = $resource['input']['db_user']['value']
$db_password = $resource['input']['db_password']['value']
$db_name = $resource['input']['db_name']['value']

$keystone_password      = $resource['input']['keystone_password']['value']
$package_ensure         = $resource['input']['package_ensure']['value']
$verbose                = $resource['input']['verbose']['value']
$debug                  = $resource['input']['debug']['value']
$bind_host              = $resource['input']['bind_host']['value']
$bind_port              = $resource['input']['bind_port']['value']
$log_file               = $resource['input']['log_file']['value']
$log_dir                = $resource['input']['log_dir']['value']
$database_connection    = $resource['input']['database_connection']['value']
$database_idle_timeout  = $resource['input']['database_idle_timeout']['value']
$auth_type              = $resource['input']['auth_type']['value']
$auth_host              = $resource['input']['auth_host']['value']
$auth_port              = $resource['input']['auth_port']['value']
$auth_admin_prefix      = $resource['input']['auth_admin_prefix']['value']
$auth_uri               = $resource['input']['auth_uri']['value']
$auth_protocol          = $resource['input']['auth_protocol']['value']
$keystone_tenant        = $resource['input']['keystone_tenant']['value']
$keystone_user          = $resource['input']['keystone_user']['value']
$pipeline               = $resource['input']['pipeline']['value']
$use_syslog             = $resource['input']['use_syslog']['value']
$log_facility           = $resource['input']['log_facility']['value']
$purge_config           = $resource['input']['purge_config']['value']
$cert_file              = $resource['input']['cert_file']['value']
$key_file               = $resource['input']['key_file']['value']
$ca_file                = $resource['input']['ca_file']['value']
$sync_db                = $resource['input']['sync_db']['value']
$mysql_module           = $resource['input']['mysql_module']['value']
$sql_idle_timeout       = $resource['input']['sql_idle_timeout']['value']
$sql_connection         = $resource['input']['sql_connection']['value']

include glance::params

class {'glance::registry':
  keystone_password      => $keystone_password,
  enabled                => true,
  manage_service         => true,
  package_ensure         => $package_ensure,
  verbose                => $verbose,
  debug                  => $debug,
  bind_host              => $bind_host,
  bind_port              => $bind_port,
  log_file               => $log_file,
  log_dir                => $log_dir,
  database_connection    => "mysql://${db_user}:${db_password}@${ip}/${db_name}",
  database_idle_timeout  => $database_idle_timeout,
  auth_type              => $auth_type,
  auth_host              => $auth_host,
  auth_port              => $auth_port,
  auth_admin_prefix      => $auth_admin_prefix,
  auth_uri               => $auth_uri,
  auth_protocol          => $auth_protocol,
  keystone_tenant        => $keystone_tenant,
  keystone_user          => $keystone_user,
  pipeline               => $pipeline,
  use_syslog             => $use_syslog,
  log_facility           => $log_facility,
  purge_config           => $purge_config,
  cert_file              => $cert_file,
  key_file               => $key_file,
  ca_file                => $ca_file,
  sync_db                => $sync_db,
  mysql_module           => $mysql_module,
  sql_idle_timeout       => $sql_idle_timeout,
}