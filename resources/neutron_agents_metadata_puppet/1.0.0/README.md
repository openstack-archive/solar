# Neutron DHCP agent puppet resource

Setup and configure Neutron metadata agent

# Parameters

https://github.com/openstack/puppet-neutron/blob/5.1.0/manifests/agents/metadata.pp

 ``auth_password``
   (required) The password for the administrative user.

 ``shared_secret``
   (required) Shared secret to validate proxies Neutron metadata requests.

 ``package_ensure``
   Ensure state of the package. Defaults to 'present'.

 ``debug``
   Debug. Defaults to false.

 ``auth_tenant``
   The administrative user's tenant name. Defaults to 'services'.

 ``auth_user``
   The administrative user name for OpenStack Networking.
   Defaults to 'neutron'.

 ``auth_url``
   The URL used to validate tokens. Defaults to 'http://localhost:35357/v2.0'.
   Note, for this resource it is decomposed to auth_host and auth_port
   due to implementation restrictions

 ``auth_insecure``
   turn off verification of the certificate for ssl (Defaults to false)

 ``auth_ca_cert``
   CA cert to check against with for ssl keystone. (Defaults to undef)

 ``auth_region``
   The authentication region. Defaults to 'RegionOne'.

 ``metadata_ip``
   The IP address of the metadata service. Defaults to '127.0.0.1'.

 ``metadata_port``
   The TCP port of the metadata service. Defaults to 8775.

 ``metadata_workers``
   (optional) Number of separate worker processes to spawn.
   The default, count of machine's processors, runs the worker thread in the
   current process.
   Greater than 0 launches that number of child processes as workers.
   The parent process manages them. Having more workers will help to improve performances.
   Defaults to: $::processorcount

 ``metadata_backlog``
   (optional) Number of backlog requests to configure the metadata server socket with.
   Defaults to 4096

 ``metadata_memory_cache_ttl``
   (optional) Specifies time in seconds a metadata cache entry is valid in
   memory caching backend.
   Set to 0 will cause cache entries to never expire.
   Set to undef or false to disable cache.
   Defaults to 5