# Cinder API resource for puppet handler
#
# source https://github.com/openstack/puppet-cinder/blob/5.1.0/manifests/api.pp
#
# Setup and configure the cinder API endpoint
#
# === Parameters
#
# [*keystone_password*]
#   The password to use for authentication (keystone)
#
# [*keystone_enabled*]
#   (optional) Use keystone for authentification
#   Defaults to true
#
# [*keystone_tenant*]
#   (optional) The tenant of the auth user
#   Defaults to services
#
# [*keystone_user*]
#   (optional) The name of the auth user
#   Defaults to cinder
#
# [*keystone_auth_host*]
#   (optional) The keystone host
#   Defaults to localhost
#
# [*keystone_auth_port*]
#   (optional) The keystone auth port
#   Defaults to 35357
#
# [*keystone_auth_protocol*]
#   (optional) The protocol used to access the auth host
#   Defaults to http.
#
# [*os_region_name*]
#   (optional) Some operations require cinder to make API requests
#   to Nova. This sets the keystone region to be used for these
#   requests. For example, boot-from-volume.
#   Defaults to undef.
#
# [*keystone_auth_admin_prefix*]
#   (optional) The admin_prefix used to admin endpoint of the auth host
#   This allow admin auth URIs like http://auth_host:35357/keystone.
#   (where '/keystone' is the admin prefix)
#   Defaults to false for empty. If defined, should be a string with a
#   leading '/' and no trailing '/'.
#
# [*service_port*]
#   (optional) The cinder api port
#   Defaults to 5000
#
# [*service_workers*]
#   (optional) Number of cinder-api workers
#   Defaults to $::processorcount
#
# [*package_ensure*]
#   (optional) The state of the package
#   Defaults to present
#
# [*bind_host*]
#   (optional) The cinder api bind address
#   Defaults to 0.0.0.0
#
# [*enabled*]
#   (optional) The state of the service
#   Defaults to true
#
# [*manage_service*]
#   (optional) Whether to start/stop the service
#   Defaults to true
#
# [*ratelimits*]
#   (optional) The state of the service
#   Defaults to undef. If undefined the default ratelimiting values are used.
#
# [*ratelimits_factory*]
#   (optional) Factory to use for ratelimiting
#   Defaults to 'cinder.api.v1.limits:RateLimitingMiddleware.factory'
#
# [*default_volume_type*]
#   (optional) default volume type to use.
#   This should contain the name of the default volume type to use.
#   If not configured, it produces an error when creating a volume
#   without specifying a type.
#   Defaults to 'false'.
#
# [*validate*]
#   (optional) Whether to validate the service is working after any service refreshes
#   Defaults to false
#
# [*validation_options*]
#   (optional) Service validation options
#   Should be a hash of options defined in openstacklib::service_validation
#   If empty, defaults values are taken from openstacklib function.
#   Default command list volumes.
#   Require validate set at True.
#   Example:
#   glance::api::validation_options:
#     glance-api:
#       command: check_cinder-api.py
#       path: /usr/bin:/bin:/usr/sbin:/sbin
#       provider: shell
#       tries: 5
#       try_sleep: 10
#   Defaults to {}
