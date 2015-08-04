# Glance (API) resource for puppet handler

Controls a live cycle of the glance entities,
like the main puppet class, auth, DB, AMQP, packages,
keystone user, role and endpoint, API service. Also configures
glance file backend.

# Parameters

source https://github.com/openstack/puppet-glance/tree/5.1.0/manifests/init.pp

   ``package_ensure``
     Ensure state for package. 
     (Optional) Defaults to 'present'.

   ``filesystem_store_datadir``
     Location where dist images are stored.
     (Optional) Defaults to /var/lib/glance/images/.

source https://github.com/openstack/puppet-glance/blob/5.1.0/manifests/api.pp

 ``keystone_password``
   (required) Password used to authentication.

 ``verbose``
   (optional) Rather to log the glance api service at verbose level.
   Default: false

 ``debug``
   (optional) Rather to log the glance api service at debug level.
   Default: false

 ``bind_host``
   (optional) The address of the host to bind to.
   Default: 0.0.0.0

 ``bind_port``
   (optional) The port the server should bind to.
   Default: 9292

 ``backlog``
   (optional) Backlog requests when creating socket
   Default: 4096

 ``workers``
   (optional) Number of Glance API worker processes to start
   Default: $::processorcount

 ``log_file``
   (optional) The path of file used for logging
   If set to boolean false, it will not log to any file.
   Default: /var/log/glance/api.log

  ``log_dir``
    (optional) directory to which glance logs are sent.
    If set to boolean false, it will not log to any directory.
    Defaults to '/var/log/glance'

 ``registry_host``
   (optional) The address used to connect to the registry service.
   Default: 0.0.0.0

 ``registry_port``
   (optional) The port of the Glance registry service.
   Default: 9191

 ``registry_client_protocol``
   (optional) The protocol of the Glance registry service.
   Default: http

 ``auth_type``
   (optional) Type is authorization being used.
   Defaults to 'keystone'

 `` auth_host``
   (optional) Host running auth service.
   Defaults to '127.0.0.1'.

 ``auth_url``
   (optional) Authentication URL.
   Defaults to 'http://localhost:5000/v2.0'.

 `` auth_port``
   (optional) Port to use for auth service on auth_host.
   Defaults to '35357'.

 `` auth_uri``
   (optional) Complete public Identity API endpoint.
   Defaults to false.

 ``auth_admin_prefix``
   (optional) Path part of the auth url.
   This allow admin auth URIs like http://auth_host:35357/keystone/admin.
   (where '/keystone/admin' is auth_admin_prefix)
   Defaults to false for empty. If defined, should be a string with a leading '/' and no trailing '/'.

 `` auth_protocol``
   (optional) Protocol to use for auth.
   Defaults to 'http'.

 ``pipeline``
   (optional) Partial name of a pipeline in your paste configuration file with the
   service name removed.
   Defaults to 'keystone+cachemanagement'.

 ``keystone_tenant``
   (optional) Tenant to authenticate to.
   Defaults to services.

 ``keystone_user``
   (optional) User to authenticate as with keystone.
   Defaults to 'glance'.

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

 ``use_syslog``
   (optional) Use syslog for logging.
   Defaults to false.

 ``log_facility``
   (optional) Syslog facility to receive log lines.
   Defaults to 'LOG_USER'.

 ``show_image_direct_url``
   (optional) Expose image location to trusted clients.
   Defaults to false.

 ``purge_config``
   (optional) Whether to set only the specified config options
   in the api config.
   Defaults to false.

 ``cert_file``
   (optinal) Certificate file to use when starting API server securely
   Defaults to false, not set

 ``key_file``
   (optional) Private key file to use when starting API server securely
   Defaults to false, not set

 ``ca_file``
   (optional) CA certificate file to use to verify connecting clients
   Defaults to false, not set

 ``mysql_module``
   (optional) Deprecated. Does nothing.

 ``known_stores``
   (optional)List of which store classes and store class locations are
    currently known to glance at startup.
    Defaults to false.
    Example: ['glance.store.filesystem.Store','glance.store.http.Store']

 ``image_cache_dir``
   (optional) Base directory that the Image Cache uses.
    Defaults to '/var/lib/glance/image-cache'.

 ``os_region_name``
   (optional) Sets the keystone region to use.
   Defaults to 'RegionOne'.

 ``validate``
   (optional) Whether to validate the service is working after any service refreshes
   Defaults to false

 ``validation_options``
   (optional) Service validation options
   Should be a hash of options defined in openstacklib::service_validation
   If empty, defaults values are taken from openstacklib function.
   Default command list images.
   Require validate set at True.
   Example:
   glance::api::validation_options:
     glance-api:
       command: check_glance-api.py
       path: /usr/bin:/bin:/usr/sbin:/sbin
       provider: shell
       tries: 5
       try_sleep: 10
   Defaults to {}