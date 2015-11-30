.. _resource_details:


Resource
========

Resource is one of the key Solar components. Resoruce definition takes place in ``meta.yaml`` file.


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

Layer that is responsible for action execution. You need to specify handler per resource, definition in ``meta.yaml`` looks like ::

  handler: puppet


Input
-----
Treat them as values that your resouce have. All needed inputs should be provided in ``meta.yaml`` for example ::

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
It allows to validate if all values are correct. ``!`` at the end of a type means that this is required (``null`` value is not valid).

* string type ``str``, ``str!``
* integer type ``int``, ``int!``
* boolean type ``bool``, ``bool!``
* complex types:

  * list of strings ``[str!]``
  * hash with values ``{a: str!}``
  * list with hashes ``[{a: str!}]``
  * list with lists ``[[]]``


Action
------
Solar wraps deployment code into actions with specific names. Actions are executed by :ref:`res-handler-term`

Several actions of resource are mandatory:
- run
- remove
- update

You can just put files into ``actions`` subdir in your resource or solar will detect them automaticaly, you can also provide actions in ``meta.yaml`` ::

    actions:
      run: run.pp
      update: run.pp

Tag
---

You can attach as many tags to resource as you want, later you can use those tags for grouping etc ::

  tags: [resource=hosts_file, tag_name=tag_value, just_some_label]
