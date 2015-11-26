==============
Solar Glossary
==============

Resources
=========

Inputs
--------
Resource configuration that will be used in actions, handlers and orchestration.
All known inputs should be provided in meta.yaml ::

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

Connections
------------
Allows to build hierarchy between inputs of several resources,
parent value will be always used in child while connection is created.
If connection will be removed - original value of child will be preserved.

Actions
--------
Solar wraps deployment code into actions with specific names.
Several actions of resource are mandatory:
- run
- remove
- update

All actions should be provided in meta.yaml ::

    actions:
      run: run.pp
      update: run.pp

Tags
------
Used to create arbitrary groups of resources, later this groups will be
used for different user operations.

Handlers
========
Layer that responsible for action execution and tracking result.
Currently handler specified in resource meta.yaml and used for all resource
actions ::

  handler: puppet

Transports
-----------
Used in handlers to communicate with managed by solar hosts. List of transports
should be added to a node. Transports will be added to a resource by means
of transports id.

Two different types of transports are used: run and sync.
Run transport - reponsible for running command on remote host.
Sync transport - uploads required information.

location_id
------------
Used in transport layer to find ip address of a node. ::

  'location_id': '96bc779540d832284680785ecd948a2d'

transports_id
------------
Used to find transports array that will be used for transport selection. ::

  'transports_id': '3889e1790e68b80b4f255cf0e13494b1'

BAT transport
--------------
According to preferences solar will choose best available transport for
file uploading and command execution.

Events
======
Used in solar to describe all possible transitions between resources changes.
Each event allows to specify two points of transitions, condition of this
transition and type of event.

Right now we are supporting 2 types of events.

1. Dependency
Inserts edge between 2 changes into the deployment plan.
2. Reaction
Inserts change specified in reaction and makes edge between parent and child.

Example ::

  type: depends_on
  parent: nova-db
  parent_action: run
  child: nova-api
  child_action: run
  state: success // condition


Virtual resources/templates
===========================
Composition layer that allows to:

- group resources
- specify connections between inputs
- add list of events

System log component
====================
Component responsible for tracking changes and keeping ordered history of
them.

Staged log
-----------
Based on user changes - solar will create log of staged changes.
This log will be used later to build deployment plan.

History
--------
After action that is related to change will be executed - it will be moved to history with same uuid.

Commited resource data
----------------------
After each succesfull change commited copy of resource data will be updated
with diff of that change.

Orchestration component
========================

Deployment plan
----------------
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

TODO link to ./orchestration.md
