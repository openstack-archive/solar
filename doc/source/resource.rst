.. _resource_details:

Resource
========

Resource is one of the key Solar components, almost every entity in Solar is a
resource. Examples are:

* packages
* services

Resources are defined in ``meta.yaml`` file. This file is responsible for basic
configuration of given resource. Below is an explanation what constitutes
typical resource.

.. TODO: change to openstack/solar-resources later
.. note::
   You can find example resources https://github.com/Mirantis/solar-resources


Basic resource structure
------------------------

.. code::

   ├── actions
   │   ├── remove.pp
   │   ├── run.pp
   │   └── update.pp
   └── meta.yaml


Handler
-------

.. TODO: add link to handlers doc there

Pluggable layer that is responsible for executing an action on resource. You
need to specify handler per every resource. Handler is defined in ``meta.yaml``
as below ::

  handler: puppet

Solar currently supports following handlers:

* puppet - first version of puppet handler (legacy, will be deprecated soon)
* puppetv2 - second, improved version of puppet, supporting hiera integration
* ansible_playbook - first version of ansible handler (legacy, will be deprecated soon)
* ansible_template - second generation of ansible implementation, includes transport support

Handlers are pluggable, so you can write your own easily to extend
functionality of Solar. Interesting examples might be Chef, SaltStack,
CFEngine etc. Using handlers allows Solar to be quickly implemented in various
environments and integrate with already used configuration management tools.

Input
-----
Inputs are essentially values that given resource can accept. Exact usage
depends on handler and actions implementation. If your handler is puppet,
inputs are basically parameters that can be accepted by puppet manifest
underneath.

All needed inputs should be defined in ``meta.yaml`` for example: ::

  input:
      keystone_password:
        schema: str!
        value: 'keystone'
      keystone_enabled:
        schema: bool
        value: true
      keystone_tenant:
        schema: str
        value: 'services'
      keystone_user:
        schema: str
        value: 'cinder'

Input schema
~~~~~~~~~~~~
Input definition contains basic schema validation that allows to validate if
all values are correct. ``!`` at the end of a type means that it is required
(``null`` value is not valid).

* string type ``str``, ``str!``
* integer type ``int``, ``int!``
* boolean type ``bool``, ``bool!``
* complex types:

  * list of strings ``[str!]``
  * hash with values ``{a: str!}``
  * list with hashes ``[{a: str!}]``
  * list with lists ``[[]]``


Input manipulation
~~~~~~~~~~~~~~~~~~
There is possibility to add and remove inputs from given resource.
To do so you can use ``solar input add`` or ``solar input remove`` in Solar CLI.


.. _computable-inputs:

Computable Inputs
-----------------
Computable input is special input type, it shares all logic that standard input has (connections etc),
but you can set a function that will return final input value.

.. note::
   Remeber, that you need to connect inputs to have it accessible in Computable Inputs logic.

Currently you can write the functions using:

- Pure Python
- Jinja2 template
- LUA

Besides that there are 2 types of Computable Inputs:

- ``values``

  - all connected inputs are passed by value as ``D`` variable

- ``full``

  - all connected inputs are passed as array (python dict type) as ``R`` variable, so you have full information about input.


In addition for ``jinja`` all connected inputs for current resource are accessible as first level variables.


Change computable input
~~~~~~~~~~~~~~~~~~~~~~~
You can change Computable Input properties by calling ``solar input change_computable`` in Solar CLI.


Action
------
Solar wraps deployment code into actions with specific names. Actions are
executed by :ref:`res-handler-term`

Several actions of resource are mandatory:

- run
- remove
- update

You can just put files into ``actions`` subdir in your resource and solar will
detect them automatically based on their names, or you can also customize
action file names in ``meta.yaml`` ::

    actions:
      run: run.pp
      update: run.pp

Tag
---

Tags are used for flexible grouping of resources. You can attach as many tags
to resource as you want, later you can use those tags for grouping etc ::

  tags: [resource=hosts_file, tag_name=tag_value, just_some_label]
