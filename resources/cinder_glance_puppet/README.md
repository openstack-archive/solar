# Cinder Volume resource for puppet handler

Glance drive Cinder as a block storage backend to store image data.

# Parameters

source https://github.com/openstack/puppet-cinder/blob/5.1.0/manifests/glance.pp

 ``glance_api_servers``
   (optional) A list of the glance api servers available to cinder.
   Should be an array with [hostname|ip]:port
   Defaults to undef
   Note: for this resource, it is decomposed to *_host and *_port due to
   existing implementation limitations

 ``glance_api_version``
   (optional) Glance API version.
   Should be 1 or 2
   Defaults to 2 (current version)

 ``glance_num_retries``
   (optional) Number retries when downloading an image from glance.
   Defaults to 0

 ``glance_api_insecure``
   (optional) Allow to perform insecure SSL (https) requests to glance.
   Defaults to false

 ``glance_api_ssl_compression``
   (optional) Whether to attempt to negotiate SSL layer compression when
   using SSL (https) requests. Set to False to disable SSL
   layer compression. In some cases disabling this may improve
   data throughput, eg when high network bandwidth is available
   and you are using already compressed image formats such as qcow2.
   Defaults to false

 ``glance_request_timeout``
   (optional) http/https timeout value for glance operations.
   Defaults to undef