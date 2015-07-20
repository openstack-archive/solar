# Cinder resource for puppet handler

Controlls a live cycle of the cinder entities,
like the main puppet class, auth, DB, AMQP, packages,
keystone user, role and endpoint.

# Parameters

source https://github.com/openstack/puppet-cinder/blob/5.1.0/manifests/init.pp

 ``database_connection``
    Url used to connect to database.
    (Optional) Defaults to
    'sqlite:////var/lib/cinder/cinder.sqlite'

 ``database_idle_timeout``
   Timeout when db connections should be reaped.
   (Optional) Defaults to 3600.

 ``database_min_pool_size``
   Minimum number of SQL connections to keep open in a pool.
   (Optional) Defaults to 1.

 ``database_max_pool_size``
   Maximum number of SQL connections to keep open in a pool.
   (Optional) Defaults to undef.

 ``database_max_retries``
   Maximum db connection retries during startup.
   Setting -1 implies an infinite retry count.
   (Optional) Defaults to 10.

 ``database_retry_interval``
   Interval between retries of opening a sql connection.
   (Optional) Defaults to 10.

 ``database_max_overflow``
   If set, use this value for max_overflow with sqlalchemy.
   (Optional) Defaults to undef.

 ``rabbit_use_ssl``
   (optional) Connect over SSL for RabbitMQ
   Defaults to false

 ``kombu_ssl_ca_certs``
   (optional) SSL certification authority file (valid only if SSL enabled).
   Defaults to undef

 ``kombu_ssl_certfile``
   (optional) SSL cert file (valid only if SSL enabled).
   Defaults to undef

 ``kombu_ssl_keyfile``
   (optional) SSL key file (valid only if SSL enabled).
   Defaults to undef

 ``kombu_ssl_version``
   (optional) SSL version to use (valid only if SSL enabled).
   Valid values are TLSv1, SSLv23 and SSLv3. SSLv2 may be
   available on some distributions.
   Defaults to 'TLSv1'

 ``amqp_durable_queues``
   Use durable queues in amqp.
   (Optional) Defaults to false.

 ``use_syslog``
   Use syslog for logging.
   (Optional) Defaults to false.

 ``log_facility``
   Syslog facility to receive log lines.
   (Optional) Defaults to LOG_USER.

 ``log_dir``
   (optional) Directory where logs should be stored.
   If set to boolean false, it will not log to any directory.
   Defaults to '/var/log/cinder'

 ``use_ssl``
   (optional) Enable SSL on the API server
   Defaults to false, not set

 ``cert_file``
   (optinal) Certificate file to use when starting API server securely
   Defaults to false, not set

 ``key_file``
   (optional) Private key file to use when starting API server securely
   Defaults to false, not set

 ``ca_file``
   (optional) CA certificate file to use to verify connecting clients
   Defaults to false, not set_

 ``mysql_module``
   (optional) Deprecated. Does nothing.

 ``storage_availability_zone``
   (optional) Availability zone of the node.
   Defaults to 'nova'

 ``default_availability_zone``
   (optional) Default availability zone for new volumes.
   If not set, the storage_availability_zone option value is used as
   the default for new volumes.
   Defaults to false

 ``sql_connection``
   DEPRECATED
 ``sql_idle_timeout``
   DEPRECATED