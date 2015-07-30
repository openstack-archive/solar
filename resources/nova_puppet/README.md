# Nova resource for puppet handler

Controlls a live cycle of the nova entities,
like the main puppet class, auth, DB, AMQP, packages,
keystone user, role and endpoint.

# Parameters

source https://github.com/openstack/puppet-nova/blob/5.1.0/manifests/init.pp

 ``ensure_package``
   (optional) The state of nova packages
   Defaults to 'present'

 ``nova_cluster_id``
   (optional) Deprecated. This parameter does nothing and will be removed.
   Defaults to 'localcluster'

 ``sql_connection``
   (optional) Deprecated. Use database_connection instead.
   Defaults to false

 ``sql_idle_timeout``
   (optional) Deprecated. Use database_idle_timeout instead
   Defaults to false

 ``database_connection``
   (optional) Connection url to connect to nova database.
   Defaults to false

 ``slave_connection``
   (optional) Connection url to connect to nova slave database (read-only).
   Defaults to false

 ``database_idle_timeout``
   (optional) Timeout before idle db connections are reaped.
   Defaults to 3600

 ``rpc_backend``
   (optional) The rpc backend implementation to use, can be:
     rabbit (for rabbitmq)
     qpid (for qpid)
     zmq (for zeromq)
   Defaults to 'rabbit'

 ``image_service``
   (optional) Service used to search for and retrieve images.
   Defaults to 'nova.image.local.LocalImageService'

 ``glance_api_servers``
   (optional) List of addresses for api servers.
   Defaults to 'localhost:9292'

 ``memcached_servers``
   (optional) Use memcached instead of in-process cache. Supply a list of memcached server IP's:Memcached Port.
   Defaults to false

 ``rabbit_host``
   (optional) Location of rabbitmq installation.
   Defaults to 'localhost'

 ``rabbit_hosts``
   (optional) List of clustered rabbit servers.
   Defaults to false

 ``rabbit_port``
   (optional) Port for rabbitmq instance.
   Defaults to '5672'

 ``rabbit_password``
   (optional) Password used to connect to rabbitmq.
   Defaults to 'guest'

 ``rabbit_userid``
   (optional) User used to connect to rabbitmq.
   Defaults to 'guest'

 ``rabbit_virtual_host``
   (optional) The RabbitMQ virtual host.
   Defaults to '/'

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
   (optional) Define queues as "durable" to rabbitmq.
   Defaults to false

 ``qpid_hostname``
   (optional) Location of qpid server
   Defaults to 'localhost'

 ``qpid_port``
   (optional) Port for qpid server
   Defaults to '5672'

 ``qpid_username``
   (optional) Username to use when connecting to qpid
   Defaults to 'guest'

 ``qpid_password``
   (optional) Password to use when connecting to qpid
   Defaults to 'guest'

 ``qpid_heartbeat``
   (optional) Seconds between connection keepalive heartbeats
   Defaults to 60

 ``qpid_protocol``
   (optional) Transport to use, either 'tcp' or 'ssl''
   Defaults to 'tcp'

 ``qpid_sasl_mechanisms``
   (optional) Enable one or more SASL mechanisms
   Defaults to false

 ``qpid_tcp_nodelay``
   (optional) Disable Nagle algorithm
   Defaults to true

 ``service_down_time``
   (optional) Maximum time since last check-in for up service.
   Defaults to 60

 ``logdir``
   (optional) Deprecated. Use log_dir instead.
   Defaults to false

 ``log_dir``
   (optional) Directory where logs should be stored.
   If set to boolean false, it will not log to any directory.
   Defaults to '/var/log/nova'

 ``state_path``
   (optional) Directory for storing state.
   Defaults to '/var/lib/nova'

 ``lock_path``
   (optional) Directory for lock files.
   On RHEL will be '/var/lib/nova/tmp' and on Debian '/var/lock/nova'
   Defaults to $::nova::params::lock_path

 ``verbose``
   (optional) Set log output to verbose output.
   Defaults to false

 ``periodic_interval``
   (optional) Seconds between running periodic tasks.
   Defaults to '60'

 ``report_interval``
   (optional) Interval at which nodes report to data store.
    Defaults to '10'

 ``monitoring_notifications``
   (optional) Whether or not to send system usage data notifications out on the message queue. Only valid for stable/essex.
   Defaults to false

 ``use_syslog``
   (optional) Use syslog for logging
   Defaults to false

 ``log_facility``
   (optional) Syslog facility to receive log lines.
   Defaults to 'LOG_USER'

 ``use_ssl``
   (optional) Enable SSL on the API server
   Defaults to false, not set

 ``enabled_ssl_apis``
   (optional) List of APIs to SSL enable
   Defaults to []
   Possible values : 'ec2', 'osapi_compute', 'metadata'

 ``cert_file``
   (optinal) Certificate file to use when starting API server securely
   Defaults to false, not set

 ``key_file``
   (optional) Private key file to use when starting API server securely
   Defaults to false, not set

 ``ca_file``
   (optional) CA certificate file to use to verify connecting clients
   Defaults to false, not set_

 ``nova_user_id``
   (optional) Create the nova user with the specified gid.
   Changing to a new uid after specifying a different uid previously,
   or using this option after the nova account already exists will break
   the ownership of all files/dirs owned by nova. It is strongly encouraged
   not to use this option and instead create user before nova class or
   for network shares create netgroup into which you'll put nova on all the
   nodes. If undef no user will be created and user creation will standardly
   happen in nova-common package.
   Defaults to undef.

 ``nova_group_id``
   (optional) Create the nova user with the specified gid.
   Changing to a new uid after specifying a different uid previously,
   or using this option after the nova account already exists will break
   the ownership of all files/dirs owned by nova. It is strongly encouraged
   not to use this option and instead create group before nova class or for
   network shares create netgroup into which you'll put nova on all the
   nodes. If undef no user or group will be created and creation will
   happen in nova-common package.
   Defaults to undef.

 ``nova_public_key``
   (optional) Install public key in .ssh/authorized_keys for the 'nova' user.
   Expects a hash of the form { type => 'key-type', key => 'key-data' } where
   'key-type' is one of (ssh-rsa, ssh-dsa, ssh-ecdsa) and 'key-data' is the
   actual key data (e.g, 'AAAA...').

 ``nova_private_key``
   (optional) Install private key into .ssh/id_rsa (or appropriate equivalent
   for key type).  Expects a hash of the form { type => 'key-type', key =>
   'key-data' }, where 'key-type' is one of (ssh-rsa, ssh-dsa, ssh-ecdsa) and
   'key-data' is the contents of the private key file.

 ``nova_shell``
   (optional) Set shell for 'nova' user to the specified value.
   Defaults to '/bin/false'.

 ``mysql_module``
   (optional) Deprecated. Does nothing.

 ``notification_driver``
   (optional) Driver or drivers to handle sending notifications.
   Value can be a string or a list.
   Defaults to []

 ``notification_topics``
   (optional) AMQP topic used for OpenStack notifications
   Defaults to 'notifications'

 ``notify_api_faults``
   (optional) If set, send api.fault notifications on caught
   exceptions in the API service
   Defaults to false

 ``notify_on_state_change``
   (optional) If set, send compute.instance.update notifications
   on instance state changes. Valid values are None for no notifications,
   "vm_state" for notifications on VM state changes, or "vm_and_task_state"
   for notifications on VM and task state changes.
   Defaults to undef

 ``os_region_name``
   (optional) Sets the os_region_name flag. For environments with
   more than one endpoint per service, this is required to make
   things such as cinder volume attach work. If you don't set this
   and you have multiple endpoints, you will get AmbiguousEndpoint
   exceptions in the nova API service.
   Defaults to undef