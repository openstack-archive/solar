# `haproxy_config` resource

This resource represents configuration for the `haproxy_service` resource.
Each service represented by Haproxy is connected to this resource via
`haproxy_service_config` resource. This is because in Haproxy there is no
support for something like `/etc/haproxy/conf.d` directory where you put
each config in a separate file, but instead you must collect all configuration
in one file.

So this resource renders this file from data provided by collecting individual
`haproxy_service_config` data.
