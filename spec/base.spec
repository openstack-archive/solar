
First draft of fully functional specification for new deployment tool.
By this specification it is proposed that new solution should be fully
plugable right from the start.

Fuel should be splitted at least in several repositories.
First one would fuel-api and will store only core api functionality
of the new tool.

Second one should be named something like fuel-core
(similarly to ansible-core-modules). This is what will be our verified
tools to deploy openstack in a way we want to deploy it.

Inventory api
==============

Do we want to reuse existing entities but in a new way? Or we need to
reconsider them? I am sure that we can do better with networking,
current solution just masks bad decisions that was done in past.

Orchestration api
====================

Resources
---------
Each resource should define deployment logic in a known (to fuel) tool,
and parameters that can be modified by user or another layer of inventory.

Services
--------
Single or several resources wrapped by additional data structure.
The primary purpose of service is to provide loose coupling between
roles and resources. And that can be achieved by using additional
parameters like endpoints.

::
  endpoints: {{node.management.ip}}:5000

Installing fully functional service is not only a matter of running
docker-compose, but as well we need to execute some additional
tasks on the host system.

One more challenge - verify that service started to work
(how and when it should be performed?)

Role
-----
Combination of services and resources.
The main reason to introduce one - is to allow user an easy way
to map nodes in the cluster to the functionality that is desired.

How to handle primary-{{role}} and {{role}} difference?

Profiles
--------

Profile is the main entity that user will work with.

Several opinionated profile will be provided by us, and they should
be valuable mainly because of our expertise in deploying openstack.

Each of this entity will have parameter that process provided data
with plugable pythonic architecture

::
  # profile handler
  handler: ansible

::
  # network_schema will require some amount of modifications and transformations, that is easier to accomplish within python code
  handler: network_schema


Modular architecture
====================

Every piece in fuel-core will be developed in a modular style,
and within that module - developer should be able to add/change
entities like:
    - deployment logic (ansible or other deployment code)
    - fuel pythonic handlers or other interfaces for pythonic plugins
    - resources
    - profiles
    - services


