# Nova compute resource for puppet handler

Setup and configure the Nova compute service.

# Parameters

source https://github.com/openstack/puppet-nova_compute/blob/5.1.0/manifests/compute.pp

 ``enabled``
   (optional) Whether to enable the nova-compute service
   Defaults to false

 ``manage_service``
   (optional) Whether to start/stop the service
   Defaults to true

 ``ensure_package``
   (optional) The state for the nova-compute package
   Defaults to 'present'

 ``vnc_enabled``
   (optional) Whether to use a VNC proxy
   Defaults to true

 ``vncserver_proxyclient_address``
   (optional) The IP address of the server running the VNC proxy client
   Defaults to '127.0.0.1'

 ``vncproxy_host``
   (optional) The host of the VNC proxy server
   Defaults to false

 ``vncproxy_protocol``
   (optional) The protocol to communicate with the VNC proxy server
   Defaults to 'http'

 ``vncproxy_port``
   (optional) The port to communicate with the VNC proxy server
   Defaults to '6080'

 ``vncproxy_path``
   (optional) The path at the end of the uri for communication with the VNC proxy server
   Defaults to '/vnc_auto.html'

 ``vnc_keymap``
   (optional) The keymap to use with VNC (ls -alh /usr/share/qemu/keymaps to list available keymaps)
   Defaults to 'en-us'

 ``force_config_drive``
   (optional) Whether to force the config drive to be attached to all VMs
   Defaults to false

 ``virtio_nic``
   (optional) Whether to use virtio for the nic driver of VMs
   Defaults to false

 ``neutron_enabled``
   (optional) Whether to use Neutron for networking of VMs
   Defaults to true

 ``network_device_mtu``
   (optional) The MTU size for the interfaces managed by nova
   Defaults to undef

 ``instance_usage_audit``
   (optional) Generate periodic compute.instance.exists notifications.
   Defaults to false

 ``instance_usage_audit_period``
   (optional) Time period to generate instance usages for.
   Time period must be hour, day, month or year
   Defaults to 'month'

  ``force_raw_images``
   (optional) Force backing images to raw format.
   Defaults to true

  ``reserved_host_memory``
   Reserved host memory
   The amount of memory in MB reserved for the host.
   Defaults to '512'

  ``compute_manager``
   Compute manager
   The driver that will manage the running instances.
   Defaults to nova.compute.manager.ComputeManager

  ``pci_passthrough_whitelist``
   (optional) Pci passthrough hash in format of:
   Defaults to undef
   Example
  "[ { 'vendor_id':'1234','product_id':'5678' },
     { 'vendor_id':'4321','product_id':'8765','physical_network':'default' } ] "

  ``default_availability_zone``
   (optional) Default compute node availability zone.
   Defaults to nova

  ``default_schedule_zone``
   (optional) Availability zone to use when user doesn't specify one.
   Defaults to undef

  ``internal_service_availability_zone``
   (optional) The availability zone to show internal services under.
   Defaults to internal
