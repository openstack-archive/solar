class {'keystone':
  verbose         => true,
  catalog_type    => 'sql',
  admin_token     => '{{ admin_token }}',
  sql_connection  => 'mysql://{{ db_user }}:{{ db_password }}@{{ ip }}/{{ db_name }}',
  public_port     => '{{ port }}'
}
