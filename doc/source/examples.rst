.. _examples:

Examples
========

Create resource for the puppet handler
--------------------------------------

Let's create an example :ref:`resource-term` for the puppet
:ref:`res-handler-term` version 1 [#]_. The resource should install and
configure OpenStack Nova API service.

.. [#] There is also puppet handler version 2 but it is out of the scope
   of this example.

Step 1: Find an appropriate puppet module
+++++++++++++++++++++++++++++++++++++++++

The `Puppet OpenStack <https://wiki.openstack.org/wiki/Puppet>`_
module for `Nova <https://github.com/openstack/puppet-nova>`_
provides all of the required functionality.

Step 2: Define granularity level for a resource
+++++++++++++++++++++++++++++++++++++++++++++++

One may want to implement resources as atomic entities doing their only single
task, like running one and only puppet manifest [#]_. Other option might be
single entity doing all required tasks instead. In order to configure and run
the Nova API service at least two manifests should be executed:
`init.pp <https://github.com/openstack/puppet-nova/blob/master/manifests/init.pp>`_
and
`api.pp <https://github.com/openstack/puppet-nova/blob/master/manifests/api.pp>`_ [#]_.

.. [#] Puppet manifests may contain references to externally defined classess
   or services in the catalog. Keep that in mind then designing the resource.

.. [#] This assumes configuring DB and messaging entities like user, password
   database, vhost, access rights are left out of the scope of this example.

Assuming the atomic tasks approach, the example resource for Nova API service
should only use the `api.pp` manifest. Note that the puppet handler is normally
executed in its own isolated puppet catalog with its specific hiera data only.
This assumes every puppet manifest called by every action to be executed as a
separate puppet run and shares nothing with other tasks.

Step 3: Define resource inputs
++++++++++++++++++++++++++++++

Once the granularity level of the resource is clearly defined, one should
define the resource's :ref:`res-input-term` data. The puppet class `nova::api`
contains lots of parameters. It looks reasonable to use them as the resource
inputs as is.

.. note ::
  There is a `helper script <https://github.com/bogdando/convert_puppet_parameters>`_
  to convert a puppet class parameters into the format expected by the
  `meta.yaml` inputs file.

Step 4: Implement basic action run
++++++++++++++++++++++++++++++++++++++

Each resource should have all of the mandatory actions defined. In this example
we define only the :ref:`ref-action-term` `run`. With the example of Nova API
resource, the action run should:

- fetch the resource inputs from the hiera [#]_ ::

      $resource = hiera($::resource_name)
      $ensure_package = $resource['input']['ensure_package']
      $auth_strategy = $resource['input']['auth_strategy']

.. [#] The syntax is the puppet handler v1 specific. The v2 allows to query
   the hiera directly, like `$public_vip = hiera('public_vip')`

- call the `class { 'nova::api': }` with the required parameters
- implement workarounds for externally referenced entities, like ::

     exec { 'post-nova_config':
       command     => '/bin/echo "Nova config has changed"',
     }

     include nova::params

     package { 'nova-common':
       name   => $nova::params::common_package_name,
       ensure => $ensure_package,
     }

.. note ::
   Otherwise, called class would assume the package and exec are
   already included in the catalog by the `init.pp`. And would fail as
   there is no `class { 'nova': }` call expected for the Nova API resource
   action run.
   In order to implement the resource without such workarounds, one should
   rethink the granularity scope for the resource. And make sure the resource
   contains required inputs for the main `nova` and `nova::api` classes and
   call them both in the resource action run.

Step 5: Think of the rest of the resource actions
+++++++++++++++++++++++++++++++++++++++++++++++++

One should also design other actions for the resource. Mandatory are only
`run`, `update` and `remove`. There might be additional ones like `on-fail`,
`on-retry` or whichever are actually required to implement expected behavior.
For the given API resource there are no specific actions expected and there
is nothing to do for the action remove. For the action update, it is likely
the same steps should be done as for the action run.

Step 6: Design the high level functional test
+++++++++++++++++++++++++++++++++++++++++++++

TODO(bogdando) provide details about test.py and writing tests for Nova API
in order to verify if it works on the app level.

Step 7: Think of the deployment composition
+++++++++++++++++++++++++++++++++++++++++++

The deployment composition is which resources should be used and in which order
it should be executed to achieve the expected result, which is a successful
:ref:`deploy-plan-term`. For the given example, the composition may be as
following:

- Install and configure MySQL DB [#]_
- Install and configure RabbitMQ node
- Install and configure dependency components like OpenStack Keystone
- Create all of the required user/tenant/db/vhost entities and assign rights
- Install and configure Nova main components, like packages, db sync, configs.
- Install and configure Nova API. BINGO! A job for our resource, at last!

.. [#] Omitted host related steps like OS provisioning, disks and network
   configuration.

Besides the execution plan, there is also data :ref:`res-connection-term`
to be considered. For example, one might want to have all of the OpenStack
services to use the common RabbitMQ virtualhost and user. Or have them
separated instead. Or use the clustered RabbitMQ nodes. These decisions
will directly impact how resources' inputs should be connected.
