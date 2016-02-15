Usage
=====

To understand a workflow you should start with our
:ref:`tutorial_wordpress`.

Solar can be used in three ways. Using CLI Api, python API and Composer files.
The last one is showed in :ref:`tutorial_wordpress`.

Examples
--------

.. note::

   You need to have nodes resources created before running example. You can add them by calling
   `solar resource create nodes templates/nodes count=X` where `X` is required nodes number

Each API is used in different examples:

Python API
~~~~~~~~~~

* `3 node cluster riak <https://github.com/openstack/solar-resources/blob/master/examples/riak/riaks.py>`_
* `hosts files <https://github.com/openstack/solar-resources/blob/master/examples/hosts_file/hosts.py>`_
* `2 node OpenStack Cluster <https://github.com/openstack/solar-resources/blob/master/examples/openstack/openstack.py>`_

Composer files
~~~~~~~~~~~~~~

* `Wordpress site <https://github.com/openstack/solar-resources/tree/master/examples/wordpress>`_
* `3 node cluster riak <https://github.com/openstack/solar-resources/blob/master/examples/riak/riak_cluster.yaml>`_


CLI API
-------

1. Create some resources (look at
   `solar-resources/examples/openstack/openstack.py`) and connect them between
   each other, and place them on nodes.
2. Run `solar changes stage` (this stages the changes)
3. Run `solar changes process` (this prepares orchestrator graph, returning
   change UUID)
4. Run `solar orch run-once <change-uuid>` (or `solar orch run-once last`
   to run the lastly created graph)
5. Observe progress of orch with `watch 'solar orch report <change-uuid>'`
   (or `watch 'solar orch report last'`).

Some very simple cluster setup:

.. code-block:: bash

  solar resource create nodes templates/nodes count=1
  solar resource create mariadb_service resources/mariadb_service '{"image": "mariadb:5.6", "root_password": "mariadb", "port": 3306}'
  solar resource create keystone_db resources/mariadb_db/ '{"db_name": "keystone_db", "login_user": "root"}'
  solar resource create keystone_db_user resources/mariadb_user/ user_name=keystone user_password=keystone  # another valid format

  solar connect node1 mariadb_service # it will mark mariadb_service to run on node1
  solar connect node1 keystone_db
  solar connect mariadb_service keystone_db '{"root_password": "login_password", "port": "login_port", "ip": "db_host"}'
  solar connect keystone_db keystone_db_user

  solar changes stage
  solar changes process
  solar orch run-once last # or solar orch run-once last
  solar orch report last -w 1000 # or solar orch report last

You can fiddle with the above configuration like this:

.. code-block:: bash

  solar resource update keystone_db_user '{"user_password": "new_keystone_password"}'
  solar resource update keystone_db_user user_password=new_keystone_password   # another valid format

  solar changes stage
  solar changes process
  solar orch run-once last

To get data for the resource `bar` (raw and pretty-JSON):

.. code-block:: bash

  solar resource show --tag 'resources/bar'
  solar resource show --as_json --tag 'resources/bar' | jq .
  solar resource show --name 'resource_name'
  solar resource show --name 'resource_name' --json | jq .

To clear all resources/connections:

.. code-block:: bash

  solar resource clear_all

Show the connections/graph:

.. code-block:: bash

  solar connections show
  solar connections graph

You can also limit graph to show only specific resources:

.. code-block:: bash

  solar connections graph --start-with mariadb_service --end-with keystone_db

You can make sure that all input values are correct and mapped without
duplicating your values with this command:

.. code-block:: bash

  solar resource validate

Disconnect

.. code-block:: bash

  solar disconnect mariadb_service node1

Tag a resource:

.. code-block:: bash

  solar resource tag node1 test-tags # Remove tags
  solar resource tag node1 test-tag --delete
