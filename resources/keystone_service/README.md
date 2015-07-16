# `keystone_service` resource

This resource sets up a Docker container with Keystone code. It requires
config to be provided by the `keystone_config` resource (mounted under
`/etc/keystone`).

Basically, the philosophy behind containers in Solar is to have stateless
containers with service code and mount stateful resources with config,
volumes, etc. to that container. Upgrade of code then would be just about
replacing the stateless container with new one and remounting state to that
new container.
