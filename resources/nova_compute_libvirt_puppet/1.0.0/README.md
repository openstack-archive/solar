# Nova compute libvirt resource for puppet handler

Install and manage nova-compute guests managed by libvirt.
Cannot be used separately from nova compute resource and
should share the same node.
Libvirt service name defaults are given for Debian OS family.

# Parameters

source https://github.com/openstack/puppet-nova_compute_libvirt/blob/5.1.0/manifests/compute/libvirt.pp

 ``libvirt_virt_type``
   (optional) Libvirt domain type. Options are: kvm, lxc, qemu, uml, xen
   Replaces libvirt_type
   Defaults to 'kvm'

 ``vncserver_listen``
   (optional) IP address on which instance vncservers should listen
   Defaults to '127.0.0.1'

 ``migration_support``
   (optional) Whether to support virtual machine migration
   Defaults to false

 ``libvirt_cpu_mode``
   (optional) The libvirt CPU mode to configure.  Possible values
   include custom, host-model, none, host-passthrough.
   Defaults to 'host-model' if libvirt_virt_type is set to either
   kvm or qemu, otherwise defaults to 'none'.

 ``libvirt_disk_cachemodes``
   (optional) A list of cachemodes for different disk types, e.g.
   ["file=directsync", "block=none"]
   If an empty list is specified, the disk_cachemodes directive
   will be removed from nova.conf completely.
   Defaults to an empty list

 ``libvirt_inject_password``
   (optional) Inject the admin password at boot time, without an agent.
   Defaults to false

 ``libvirt_inject_key``
   (optional) Inject the ssh public key at boot time.
   Defaults to false

 ``libvirt_inject_partition``
   (optional) The partition to inject to : -2 => disable, -1 => inspect
   (libguestfs only), 0 => not partitioned, >0 => partition
   number (integer value)
   Defaults to -2

 ``remove_unused_base_images``
   (optional) Should unused base images be removed?
   If undef is specified, remove the line in nova.conf
   otherwise, use a boolean to remove or not the base images.
   Defaults to undef

 ``remove_unused_kernels``
   (optional) Should unused kernel images be removed?
   This is only safe to enable if all compute nodes
   have been updated to support this option.
   If undef is specified, remove the line in nova.conf
   otherwise, use a boolean to remove or not the kernels.
   Defaults to undef

 ``remove_unused_resized_minimum_age_seconds``
   (optional) Unused resized base images younger
   than this will not be removed
   If undef is specified, remove the line in nova.conf
   otherwise, use a integer or a string to define after
   how many seconds it will be removed.
   Defaults to undef

 ``remove_unused_original_minimum_age_seconds``
   (optional) Unused unresized base images younger
   than this will not be removed
   If undef is specified, remove the line in nova.conf
   otherwise, use a integer or a string to define after
   how many seconds it will be removed.
   Defaults to undef

 ``libvirt_service_name``
   (optional) libvirt service name.
   Defaults to $::nova::params::libvirt_service_name
