# Nova conductor resource for puppet handler

Setup and configure the Nova conductor service.
Note, it [should not](http://docs.openstack.org/juno/config-reference/content/section_conductor.html) be deployed on compute nodes.

# Parameters

source https://github.com/openstack/puppet-nova_conductor/blob/5.1.0/manifests/conductor.pp

 ``ensure_package``
   (optional) The state of the nova conductor package
   Defaults to 'present'

 ``workers``
   (optional) Number of workers for OpenStack Conductor service
   Defaults to undef (i.e. parameter will not be present)