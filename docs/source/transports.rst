.. _transports_details:


Transports
==========

Transports are used by Solar to communicate with managed nodes.
Transports are also resuorces, so they have all features of it.
Transports should be added to a node, but if you need you can add different transports for different resources.


How it works
------------

* Each resource in solar have randomly generated :ref:`transports-id-term`, when you connect resources together,
* Solar will ensure that correct `transport_id` is passed around. then using this `transport_id` a correct real value is fetched.
* Changing transports contents will not cause resource.update action for related resources.

Sync transport
--------------

It uploads required information to target node.

Currently there are following sync transports available:

* ssh
* rsync
* solar_agent
* torrent


Run transport
-------------

It is responsible for running command on remote host.

Currently there are following run transports available:

* ssh
* solar_agent



BAT transport
-------------

A transport that will automaticaly select best available transport (BAT) that is available for given resource. Currently it's default enabled transport, so when you add more transports to your system, then everything happens automaticaly.
