.. _transports_details:


Transports
==========

Transports are used by Solar to communicate with managed nodes.
Transports are also resources, so they have all resources features and
flexibility.
Transports should be added to a node, but if you need you can add different
transports for different resources.

How it works
------------

Each resource in solar has a random :ref:`transports-id-term` generated,
when resources are connected to each other. Solar will ensure that correct
`transport_id` is used. Then using this `transport_id` a correct real value is
fetched. Changing transports contents will not cause `resource.update` action
for related resources.

Sync transport
--------------

This transport uploads required information to target node.

Currently there are following sync transports available:

* ssh
* rsync
* solar_agent
* torrent

Ssh host key checking
---------------------
Solar wont disable strict host key checking by default, so before working with
solar ensure that strict host key checking is disabled, or all target hosts
added to .ssh/known_hosts file.

Example of .ssh/config ::

  Host 10.0.0.*
    StrictHostKeyChecking no

Run transport
-------------

This transport is responsible for running commands on remote host.

Currently there are following run transports available:

* ssh
* solar_agent

BAT transport
-------------

A transport that will automatically select best available transport (BAT) that
is available for a given resource. Currently it's default transport in the
system, so when you add more transports, everything should configure
automatically.
