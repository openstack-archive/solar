# Glance registry resource for puppet handler

Configures glance registry service.

# Parameters

source https://github.com/openstack/puppet-glance/tree/5.1.0/manifests/registry.pp

  ``keystone_password``
    (required) The keystone password for administrative user

  ``package_ensure``
    (optional) Ensure state for package. Defaults to 'present'.  On RedHat
    platforms this setting is ignored and the setting from the glance class is
    used because there is only one glance package.

  ``verbose``
    (optional) Enable verbose logs (true|false). Defaults to false.

  ``debug``
    (optional) Enable debug logs (true|false). Defaults to false.

  ``bind_host``
    (optional) The address of the host to bind to. Defaults to '0.0.0.0'.

  ``bind_port``
    (optional) The port the server should bind to. Defaults to '9191'.

  ``log_file``
    (optional) Log file for glance-registry.
    If set to boolean false, it will not log to any file.
    Defaults to '/var/log/glance/registry.log'.

  ``log_dir``
    (optional) directory to which glance logs are sent.
    If set to boolean false, it will not log to any directory.
    Defaults to '/var/log/glance'

 ``sql_idle_timeout``
   (optional) Deprecated. Use database_idle_timeout instead
   Defaults to false

 ``sql_connection``
   (optional) Deprecated. Use database_connection instead.
   Defaults to false

 ``database_connection``
   (optional) Connection url to connect to nova database.
   Defaults to 'sqlite:///var/lib/glance/glance.sqlite'

 ``database_idle_timeout``
   (optional) Timeout before idle db connections are reaped.
   Defaults to 3600

  ``auth_type``
    (optional) Authentication type. Defaults to 'keystone'.

  ``auth_host``
    (optional) Address of the admin authentication endpoint.
    Defaults to '127.0.0.1'.

  ``auth_port``
    (optional) Port of the admin authentication endpoint. Defaults to '35357'.

  ``auth_admin_prefix``
    (optional) path part of the auth url.
    This allow admin auth URIs like http://auth_host:35357/keystone/admin.
    (where '/keystone/admin' is auth_admin_prefix)
    Defaults to false for empty. If defined, should be a string with a leading '/' and no trailing '/'.

  ``auth_protocol``
    (optional) Protocol to communicate with the admin authentication endpoint.
    Defaults to 'http'. Should be 'http' or 'https'.

  ``auth_uri``
    (optional) Complete public Identity API endpoint.

  ``keystone_tenant``
    (optional) administrative tenant name to connect to keystone.
    Defaults to 'services'.

  ``keystone_user``
    (optional) administrative user name to connect to keystone.
    Defaults to 'glance'.

  ``use_syslog``
    (optional) Use syslog for logging.
    Defaults to false.

  ``log_facility``
    (optional) Syslog facility to receive log lines.
    Defaults to LOG_USER.

  ``purge_config``
    (optional) Whether to create only the specified config values in
    the glance registry config file.
    Defaults to false.

 ``cert_file``
   (optinal) Certificate file to use when starting registry server securely
   Defaults to false, not set

 ``key_file``
   (optional) Private key file to use when starting registry server securely
   Defaults to false, not set

 ``ca_file``
   (optional) CA certificate file to use to verify connecting clients
   Defaults to false, not set

 ``sync_db``
   (Optional) Run db sync on the node.
   Defaults to true

  ``mysql_module``
  (optional) Deprecated. Does nothing.
