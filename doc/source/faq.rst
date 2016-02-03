.. _faq:


FAQ
===


.. _faq_hardcoded_params:

Why nodes/transports have hardcoded keys, ips and other inputs ?
--------------------------------------------------------------

This is temporary situation, we will improve it in near future.

I want to use different SSH keys
----------------------------

Just update resource for example::

    solar resource update ssh_transport1 '{"key": "/path/to/some/key"}'

I want to use passwords not keys
--------------------------------

Just update resource::

    solar resource update rsync1 '{"password": "vagrant", "key": null}'

.. note::

   You need to change it for all transport resources (ssh and rsync by default).


How can I run solar worker ?
-----------------------------------

- If you use `vagrant` then you can just `sudo start solar-worker`
as `vagrant` user.

How can I configure solar ?
---------------------------

Solar uses oslo.config for configuration, it means that by default
solar will find config files matched by following patterns::

    ~/.solar/*.conf
    /etc/solar/*.conf

Additionally user is able to specify SOLAR_CONFIG environment variable.

.. _faq_what_database:

What database can I use with solar ?
------------------------------------

By default for simplicity we use `sqlite`. On our vagrant environment we use
single node `riak`.
You can also use multiple nodes `riak`, with some strong consistent buckets.


Where can I find solar examples ?
---------------------------------

Example resources, composer templates and examples itself are located:
https://github.com/Mirantis/solar-resources
