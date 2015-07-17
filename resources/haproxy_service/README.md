# `haproxy_service` resource

This resource sets up a Docker container with Haproxy code. It requires
config to be provided by the `haproxy_config` resource (mounted under
`/etc/haproxy`).

About container philosophy, see the `README.md` file in `keystone_service`
resource.
