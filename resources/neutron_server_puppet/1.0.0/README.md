# Neutron puppet resource

Setup and configure the neutron API service and endpoint

# Parameters:

source https://github.com/openstack/puppet-neutron/blob/5.1.0/manifests/server.pp

 ``package_ensure``
   (optional) The state of the package
   Defaults to present

 ``log_file``
   REMOVED: Use log_file of neutron class instead.

 ``log_dir``
   REMOVED: Use log_dir of neutron class instead.

 ``auth_password``
   (optional) The password to use for authentication (keystone)
   Defaults to false. Set a value unless you are using noauth

 ``auth_type``
   (optional) What auth system to use
   Defaults to 'keystone'. Can other be 'noauth'

 ``auth_host``
   (optional) The keystone host
   Defaults to localhost

 ``auth_protocol``
   (optional) The protocol used to access the auth host
   Defaults to http.

 ``auth_port``
   (optional) The keystone auth port
   Defaults to 35357

 ``auth_admin_prefix``
   (optional) The admin_prefix used to admin endpoint of the auth host
   This allow admin auth URIs like http://auth_host:35357/keystone.
   (where '/keystone' is the admin prefix)
   Defaults to false for empty. If defined, should be a string with a leading '/' and no trailing '/'.

 ``auth_tenant``
   (optional) The tenant of the auth user
   Defaults to services

 ``auth_user``
   (optional) The name of the auth user
   Defaults to neutron

 ``auth_protocol``
   (optional) The protocol to connect to keystone
   Defaults to http

 ``auth_uri``
   (optional) Complete public Identity API endpoint.
   Defaults to: $auth_protocol://$auth_host:5000/

 ``database_connection``
   (optional) Connection url for the neutron database.
   (Defaults to 'sqlite:////var/lib/neutron/ovs.sqlite')
   Note: for this resource it is decomposed to the
   'db_host', 'db_port', 'db_user', 'db_password' inputs
   due to implementation limitations

 ``database_max_retries``
   (optional) Maximum database connection retries during startup.
   (Defaults to 10)

 ``sql_max_retries``
   DEPRECATED: Use database_max_retries instead.

 ``max_retries``
   DEPRECATED: Use database_max_retries instead.

 ``database_idle_timeout``
   (optional) Timeout before idle database connections are reaped.
   Deprecates sql_idle_timeout
   (Defaults to 3600)

 ``sql_idle_timeout``
   DEPRECATED: Use database_idle_timeout instead.

 ``idle_timeout``
   DEPRECATED: Use database_idle_timeout instead.

 ``database_retry_interval``
   (optional) Interval between retries of opening a database connection.
   (Defaults to 10)

 ``sql_reconnect_interval``
   DEPRECATED: Use database_retry_interval instead.

 ``retry_interval``
   DEPRECATED: Use database_retry_interval instead.

 ``database_min_pool_size``
   (optional) Minimum number of SQL connections to keep open in a pool.
   Defaults to: 1

 ``database_max_pool_size``
   (optional) Maximum number of SQL connections to keep open in a pool.
   Defaults to: 10

 ``database_max_overflow``
   (optional) If set, use this value for max_overflow with sqlalchemy.
   Defaults to: 20

 ``sync_db``
   (optional) Run neutron-db-manage on api nodes after installing the package.
   Defaults to false

 ``api_workers``
   (optional) Number of separate worker processes to spawn.
   The default, count of machine's processors, runs the worker thread in the
   current process.
   Greater than 0 launches that number of child processes as workers.
   The parent process manages them.
   Defaults to: $::processorcount

 ``rpc_workers``
   (optional) Number of separate RPC worker processes to spawn.
   The default, count of machine's processors, runs the worker thread in the
   current process.
   Greater than 0 launches that number of child processes as workers.
   The parent process manages them.
   Defaults to: $::processorcount

 ``agent_down_time``
   (optional) Seconds to regard the agent as down; should be at least twice
   report_interval, to be sure the agent is down for good.
   agent_down_time is a config for neutron-server, set by class neutron::server
   report_interval is a config for neutron agents, set by class neutron
   Defaults to: 75

 ``router_scheduler_driver``
   (optional) Driver to use for scheduling router to a default L3 agent. Could be:
   neutron.scheduler.l3_agent_scheduler.ChanceScheduler to schedule a router in a random way
   neutron.scheduler.l3_agent_scheduler.LeastRoutersScheduler to allocate on an L3 agent with the least number of routers bound.
   Defaults to: neutron.scheduler.l3_agent_scheduler.ChanceScheduler

 ``mysql_module``
   (optional) Deprecated. Does nothing.

 ``router_distributed``
   (optional) Setting the "router_distributed" flag to "True" will default to the creation
   of distributed tenant routers.
   Also can be the type of the router on the create request (admin-only attribute).
   Defaults to false

 ``l3_ha``
   (optional) Enable high availability for virtual routers.
   Defaults to false

 ``max_l3_agents_per_router``
   (optional) Maximum number of l3 agents which a HA router will be scheduled on. If set to '0', a router will be scheduled on every agent.
   Defaults to '3'

 ``min_l3_agents_per_router``
   (optional) Minimum number of l3 agents which a HA router will be scheduled on.
   Defaults to '2'

 ``l3_ha_net_cidr``
   (optional) CIDR of the administrative network if HA mode is enabled.
   Defaults to '169.254.192.0/18'