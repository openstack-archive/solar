# Nova neutron resource for puppet handler

Setup and configure the Nova compute to use Neutron.
Note, it should only be deployed on compute nodes.
Also manage the network driver to use for compute guests
This will use virtio for VM guests and the specified driver for the VIF.

# Parameters

source https://github.com/openstack/puppet-nova/blob/5.1.0/manifests/compute/neutron.pp

 ``libvirt_vif_driver``
   (optional) The libvirt VIF driver to configure the VIFs.
   Defaults to 'nova.virt.libvirt.vif.LibvirtGenericVIFDriver'.

 ``force_snat_range``
  (optional) Force SNAT rule to specified network for nova-network
  Default to 0.0.0.0/0
  Due to architecture constraints in nova_config, it's not possible to setup
  more than one SNAT rule though initial parameter is MultiStrOpt

source https://github.com/openstack/puppet-nova/blob/5.1.0/manifests/network/neutron.pp

 ``neutron_admin_password``
   (required) Password for connecting to Neutron network services in
   admin context through the OpenStack Identity service.

 ``neutron_auth_strategy``
   (optional) Should be kept as default 'keystone' for all production deployments.
   Defaults to 'keystone'

 ``neutron_url``
   (optional) URL for connecting to the Neutron networking service.
   Defaults to 'http://127.0.0.1:9696'
   Note: for this resource it is decomposed to the
   'neutron_endpoint_host', 'neutron_endpoint_port', 'neutron_endpoint_protocol' inputs
   due to implementation limitations

 ``neutron_url_timeout``
   (optional) Timeout value for connecting to neutron in seconds.
   Defaults to '30'

 ``neutron_admin_tenant_name``
   (optional) Tenant name for connecting to Neutron network services in
   admin context through the OpenStack Identity service.
   Defaults to 'services'

 ``neutron_default_tenant_id``
   (optional) Default tenant id when creating neutron networks
   Defaults to 'default'

 ``neutron_region_name``
   (optional) Region name for connecting to neutron in admin context
   through the OpenStack Identity service.
   Defaults to 'RegionOne'

 ``neutron_admin_username``
   (optional) Username for connecting to Neutron network services in admin context
   through the OpenStack Identity service.
   Defaults to 'neutron'

 ``neutron_ovs_bridge``
   (optional) Name of Integration Bridge used by Open vSwitch
   Defaults to 'br-int'

 ``neutron_extension_sync_interval``
   (optional) Number of seconds before querying neutron for extensions
   Defaults to '600'

 ``neutron_ca_certificates_file``
   (optional) Location of ca certicates file to use for neutronclient requests.
   Defaults to 'None'

 ``neutron_admin_auth_url``
   (optional) Points to the OpenStack Identity server IP and port.
   This is the Identity (keystone) admin API server IP and port value,
   and not the Identity service API IP and port.
   Defaults to 'http://127.0.0.1:35357/v2.0'
   Note: for this resource it is decomposed to the
   'auth_host', 'auth_port', 'auth_protocol' inputs
   due to implementation limitations

 ``network_api_class``
   (optional) The full class name of the network API class.
   The default configures Nova to use Neutron for the network API.
   Defaults to 'nova.network.neutronv2.api.API'

 ``security_group_api``
   (optional) The full class name of the security API class.
   The default configures Nova to use Neutron for security groups.
   Set to 'nova' to use standard Nova security groups.
   Defaults to 'neutron'

 ``firewall_driver``
   (optional) Firewall driver.
   This prevents nova from maintaining a firewall so it does not interfere
   with Neutron's. Set to 'nova.virt.firewall.IptablesFirewallDriver'
   to re-enable the Nova firewall.
   Defaults to 'nova.virt.firewall.NoopFirewallDriver'

 ``vif_plugging_is_fatal``
   (optional) Fail to boot instance if vif plugging fails.
   This prevents nova from booting an instance if vif plugging notification
   is not received from neutron.
   Defaults to 'True'

 ``vif_plugging_timeout``
   (optional) Number of seconds to wait for neutron vif plugging events.
   Set to '0' and vif_plugging_is_fatal to 'False' if vif plugging
   notification is not being used.
   Defaults to '300'

 ``dhcp_domain``
   (optional) domain to use for building the hostnames
   Defaults to 'novalocal'