# Nova API resource for puppet handler

Setup and configure the Nova API service

# Parameters

source https://github.com/openstack/puppet-nova_api/blob/5.1.0/manifests/api.pp

 ``admin_password``
   (required) The password to set for the nova admin user in keystone

 ``ensure_package``
   (optional) Whether the nova api package will be installed
   Defaults to 'present'

 ``auth_strategy``
   (DEPRECATED) Does nothing and will be removed in Icehouse
   Defaults to false

 ``auth_host``
   (optional) The IP of the server running keystone
   Defaults to '127.0.0.1'

 ``auth_port``
   (optional) The port to use when authenticating against Keystone
   Defaults to 35357

 ``auth_protocol``
   (optional) The protocol to use when authenticating against Keystone
   Defaults to 'http'

 ``auth_uri``
   (optional) The uri of a Keystone service to authenticate against
   Defaults to false

 ``auth_admin_prefix``
   (optional) Prefix to prepend at the beginning of the keystone path
   Defaults to false

 ``auth_version``
   (optional) API version of the admin Identity API endpoint
   for example, use 'v3.0' for the keystone version 3.0 api
   Defaults to false

 ``admin_tenant_name``
   (optional) The name of the tenant to create in keystone for use by the nova services
   Defaults to 'services'

 ``admin_user``
   (optional) The name of the user to create in keystone for use by the nova services
   Defaults to 'nova'

 ``api_bind_address``
   (optional) IP address for nova-api server to listen
   Defaults to '0.0.0.0'

 ``metadata_listen``
   (optional) IP address  for metadata server to listen
   Defaults to '0.0.0.0'

 ``enabled_apis``
   (optional) A comma separated list of apis to enable
   Defaults to 'ec2,osapi_compute,metadata'

 ``keystone_ec2_url``
   (optional) The keystone url where nova should send requests for ec2tokens
   Defaults to false

 ``volume_api_class``
   (optional) The name of the class that nova will use to access volumes. Cinder is the only option.
   Defaults to 'nova.volume.cinder.API'

 ``use_forwarded_for``
   (optional) Treat X-Forwarded-For as the canonical remote address. Only
   enable this if you have a sanitizing proxy.
   Defaults to false

 ``osapi_compute_workers``
   (optional) Number of workers for OpenStack API service
   Defaults to $::processorcount

 ``ec2_workers``
   (optional) Number of workers for EC2 service
   Defaults to $::processorcount

 ``metadata_workers``
   (optional) Number of workers for metadata service
   Defaults to $::processorcount

 ``conductor_workers``
   (optional) DEPRECATED. Use workers parameter of nova::conductor
   Class instead.
   Defaults to undef

 ``sync_db``
   (optional) Run nova-manage db sync on api nodes after installing the package.
   Defaults to true

 ``neutron_metadata_proxy_shared_secret``
   (optional) Shared secret to validate proxies Neutron metadata requests
   Defaults to undef

 ``pci_alias``
   (optional) Pci passthrough for controller:
   Defaults to undef
   Example
   "[ {'vendor_id':'1234', 'product_id':'5678', 'name':'default'}, {...} ]"

 ``ratelimits``
   (optional) A string that is a semicolon-separated list of 5-tuples.
   See http://docs.openstack.org/trunk/config-reference/content/configuring-compute-API.html
   Example: '(POST, "*", .*, 10, MINUTE);(POST, "*/servers", ^/servers, 50, DAY);(PUT, "*", .*, 10, MINUTE)'
   Defaults to undef

 ``ratelimits_factory``
   (optional) The rate limiting factory to use
   Defaults to 'nova.api.openstack.compute.limits:RateLimitingMiddleware.factory'

 ``osapi_v3``
   (optional) Enable or not Nova API v3
   Defaults to false

 ``validate``
   (optional) Whether to validate the service is working after any service refreshes
   Defaults to false

 ``validation_options``
   (optional) Service validation options
   Should be a hash of options defined in openstacklib::service_validation
   If empty, defaults values are taken from openstacklib function.
   Default command list nova flavors.
   Require validate set at True.
   Example:
   nova::api::validation_options:
     nova-api:
       command: check_nova.py
       path: /usr/bin:/bin:/usr/sbin:/sbin
       provider: shell
       tries: 5
       try_sleep: 10
   Defaults to {}
