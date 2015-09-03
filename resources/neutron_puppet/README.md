# Neutron puppet resource

 Installs the neutron package and configures
 /etc/neutron/neutron.conf for SSL, AMQP, logging, service plugins and other stuff.
 Does not produce any services.

# Parameters:

source https://github.com/openstack/puppet-neutron/blob/5.1.0/manifests/init.pp

 ``package_ensure``
   (optional) The state of the package
   Defaults to 'present'

 ``verbose``
   (optional) Verbose logging
   Defaults to False

 ``debug``
   (optional) Print debug messages in the logs
   Defaults to False

 ``bind_host``
   (optional) The IP/interface to bind to
   Defaults to 0.0.0.0 (all interfaces)

 ``bind_port``
   (optional) The port to use
   Defaults to 9696

 ``core_plugin``
   (optional) Neutron plugin provider
   Defaults to openvswitch
   Could be bigswitch, brocade, cisco, embrane, hyperv, linuxbridge, midonet, ml2, mlnx, nec, nicira, plumgrid, ryu

 ``service_plugins``
   (optional) Advanced service modules.
   Could be an array that can have these elements:
   router, firewall, lbaas, vpnaas, metering
   Defaults to empty

 ``auth_strategy``
   (optional) How to authenticate
   Defaults to 'keystone'. 'noauth' is the only other valid option

 ``base_mac``
   (optional) The MAC address pattern to use.
   Defaults to fa:16:3e:00:00:00

 ``mac_generation_retries``
   (optional) How many times to try to generate a unique mac
   Defaults to 16

 ``dhcp_lease_duration``
   (optional) DHCP lease
   Defaults to 86400 seconds

 ``dhcp_agents_per_network``
   (optional) Number of DHCP agents scheduled to host a network.
   This enables redundant DHCP agents for configured networks.
   Defaults to 1

 ``network_device_mtu``
   (optional) The MTU size for the interfaces managed by neutron
   Defaults to undef

 ``dhcp_agent_notification``
   (optional) Allow sending resource operation notification to DHCP agent.
   Defaults to true

 ``allow_bulk``
   (optional) Enable bulk crud operations
   Defaults to true

 ``allow_pagination``
   (optional) Enable pagination
   Defaults to false

 ``allow_sorting``
   (optional) Enable sorting
   Defaults to false

 ``allow_overlapping_ips``
   (optional) Enables network namespaces
   Defaults to false

 ``api_extensions_path``
   (optional) Specify additional paths for API extensions that the
   module in use needs to load.
   Defaults to undef

 ``report_interval``
   (optional) Seconds between nodes reporting state to server; should be less than
   agent_down_time, best if it is half or less than agent_down_time.
   agent_down_time is a config for neutron-server, set by class neutron::server
   report_interval is a config for neutron agents, set by class neutron
   Defaults to: 30

 ``control_exchange``
   (optional) What RPC queue/exchange to use
   Defaults to neutron

 ``rpc_backend``
   (optional) what rpc/queuing service to use
   Defaults to impl_kombu (rabbitmq)

 ``rabbit_password``
 ``rabbit_host``
 ``rabbit_port``
 ``rabbit_user``
   (optional) Various rabbitmq settings

 ``rabbit_hosts``
   (optional) array of rabbitmq servers for HA.
   A single IP address, such as a VIP, can be used for load-balancing
   multiple RabbitMQ Brokers.
   Defaults to false

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

 ``kombu_reconnect_delay``
   (optional) The amount of time to wait before attempting to reconnect
   to MQ provider. This is used in some cases where you may need to wait
   for the provider to propery premote the master before attempting to
   reconnect. See https://review.openstack.org/#/c/76686
   Defaults to '1.0'

 ``qpid_hostname``
 ``qpid_port``
 ``qpid_username``
 ``qpid_password``
 ``qpid_heartbeat``
 ``qpid_protocol``
 ``qpid_tcp_nodelay``
 ``qpid_reconnect``
 ``qpid_reconnect_timeout``
 ``qpid_reconnect_limit``
 ``qpid_reconnect_interval``
 ``qpid_reconnect_interval_min``
 ``qpid_reconnect_interval_max``
   (optional) various QPID options

 ``use_ssl``
   (optinal) Enable SSL on the API server
   Defaults to false, not set

 ``cert_file``
   (optinal) certificate file to use when starting api server securely
   defaults to false, not set

 ``key_file``
   (optional) Private key file to use when starting API server securely
   Defaults to false, not set

 ``ca_file``
   (optional) CA certificate file to use to verify connecting clients
   Defaults to false, not set

 ``use_syslog``
   (optional) Use syslog for logging
   Defaults to false

 ``log_facility``
   (optional) Syslog facility to receive log lines
   Defaults to LOG_USER

 ``log_file``
   (optional) Where to log
   Defaults to false

 ``log_dir``
   (optional) Directory where logs should be stored
   If set to boolean false, it will not log to any directory
   Defaults to /var/log/neutron
