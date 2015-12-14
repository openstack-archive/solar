.. _glossary:

==============
Solar Glossary
==============

.. _resource-term:

Resource
========

Resource is an abstraction of item in system managed by Solar. It's a basic
building block used to assemble your system. Almost every entity in Solar
is a resource.

You can learn more about it in :ref:`resource details <resource_details>`

.. _res-input-term:

Input
-----
Resource configuration that will be used in actions, handlers and
orchestration. All known inputs for a resource should be defined in meta.yaml

.. _res-connection-term:

Connection
----------
Allows to build hierarchy between inputs of several resources, parent value
will be always used in child while connection is created. If connection is
removed - original value of child will be preserved.

.. _res-action-term:

Action
------
Solar wraps deployment code into actions with specific names. Actions are
executed from the resource.

.. _res-tag-term:

Tag
---
Used to create arbitrary groups of resources, later this groups will be
used for different user operations.

.. _res-repository-term:

Resource Repository
-------------------

It is a named location where different :ref:`resource-term` are located.

.. _res-handler-term:

Handler
=======

Layer responsible for action execution and tracking results.

.. _res-transports-term:

Transport
=========

Used in handlers to communicate with hosts managed by Solar.

.. seealso::

   :ref:`More details about transports <transports_details>`


.. _location-id-term:

location_id
-----------
Used in transport layer to find ip address of a node. ::

  'location_id': '96bc779540d832284680785ecd948a2d'

.. _transports-id-term:

transports_id
-------------
Used to find transports array that will be used for transport selection. ::

  'transports_id': '3889e1790e68b80b4f255cf0e13494b1'


BAT transport
-------------
According to preferences solar will choose best available transport for
file uploading and command execution.

.. _res-event-term:

Event
=====

Used in solar to describe all possible transitions between resources changes.
Each event allows to specify two points of transitions, condition of this
transition and type of event.

Right now we are supporting 2 types of events:

1. Dependency - inserts edge between 2 changes into the deployment plan.
2. Reaction - inserts change specified in reaction and makes edge between parent and child.

Example ::

  type: depends_on
  parent: nova-db
  parent_action: run
  child: nova-api
  child_action: run
  state: success // condition

.. _res-virtual-term:

Virtual resource/template
=========================

Composition layer that allows user to:

- group resources
- specify connections between inputs
- add list of events

.. _system-log-term:

System log component
====================

Component responsible for tracking changes and keeping ordered history of
them.

Staged log
----------
Based on user changes - solar will create log of staged changes.
This log will be used later to build deployment plan.

History
-------
After action that is related to change will be executed - it will be moved to
history with same uuid.

Committed resource data
-----------------------
After each successful change committed copy of resource data will be updated
with diff of that change.

.. _orch-term:

Orchestration component
=======================

.. _deploy-plan-term:

Deployment plan
---------------
Based on changes tracked by system log and configured events - solar build
deployment plan. In general deployment plan is built with ::

  solar ch process

And can be viewed with ::

  solar or dg last

Deployment plan operations
--------------------------
Solar cli provides several commands to work with deployment plan.

- run-once
- report
- stop
- resume/restart/retry

See also :ref:`orchestration`
