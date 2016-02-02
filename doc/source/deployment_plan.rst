.. _deployment_plan:

Preparing deployment plan
=========================

Solar allows you to make transitions between different versions of
infrastructure based on changes found by solar control plane and events
configured between this changes.

Required information
----------------------

* :ref:`resource_input`
* :ref:`orchestration`


Changes
--------

By changes in solar we understand everything that is explicitly made by
user (human/program). Examples of changes are:
- create resource
- remove resource
- update value manually
- update value using hierarchy

Staged changes
---------------

On demand solar runs procedure that will find all resources changed from last
deployment and will determine list of actions using transitions from solar
state machine .

This procedure is performed by ::

    solar changes stage -d

It prints information like ::

    log task=openrc_file.run uid=e852455d-49d9-41f1-b49c-4640e2e19944
        ++ ip: 10.0.0.3
        ++ location_id: 694b35afa622da857f95e14a21599d81
        ++ keystone_port: 35357
        ++ transports_id: abc7745f2ad63709b5845cecfa759ff5
        ++ keystone_host: 10.0.0.3
        ++ password: admin
        ++ user_name: admin
        ++ tenant: admin
    log task=neutron_db.run uid=95cac02b-01d0-4e2f-adb9-4205a2cf6dfb
        ++ login_port: 3306
        ++ encoding: utf8
        ++ login_user: root
        ++ login_password: mariadb
        ++ transports_id: abc7745f2ad63709b5845cecfa759ff5
        ++ db_name: neutron_db
        ++ db_host: 10.0.0.3
        ++ ip: 10.0.0.3
        ++ collation: utf8_general_ci
        ++ location_id: 694b35afa622da857f95e14a21599d81

At this point information is stored as a list, and user doesn't know anything
about dependencies between found changes.

Events usage
-------------

For events definition see :ref:`res-event-term`.

Events are used during this procedure to insert dependencies between found
changes, and to add new actions that are reactions for changes.

Example of dependency between changes would be *nova service* that depends
on successful creation of *database*.

For removal we might add dependencies that will allow reverse order, e.g. when
removing *nova service* and *database*, *database* will be removed only after
successful *nova service* removal.

This can be specified as ::

    Dependency database1.run -> nova1.run
    Dependency nova1.remove -> database1.remove

Reaction allows to construct more advanced workflows that will take into
account not only changes, but also arbitrary actions for resources in solar.

Good example of usage is provisioning procedure, where reboot must be
done only after node is provisioned, and dnsmasq configuration changes to
reflect that that node is now using statically allocated address.
We can specify such ordering as ::

    React node1.run -> node1.reboot
    React node1.run -> dnsmasq1.change_ip
    Dependency dnsmasq1.change_ip -> node1.reboot

Deployment plan construction
-----------------------------

Using list of staged changes and graph events we can proceed with construction
of deployment plan for current version of infrastructure ::

    solar changes process

After this deployment command plan can be viewed by ::

    # graphviz representation
    solar orch dg last

    # text report
    solar orch report last

