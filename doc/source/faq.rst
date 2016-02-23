.. _faq:


FAQ
===


.. _faq_hardcoded_params:

Why nodes/transports have hardcoded keys, ips and other inputs ?
----------------------------------------------------------------

This is temporary situation, we will improve it in near future.

.. _faq_different_ssh_keys:

I want to use different SSH keys
--------------------------------

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

There are several places where we search for config values:

1. `.config` file in CWD or in path from `SOLAR_CONFIG` env variable
2. if env `SOLAR_CONFIG_OVERRIDE` contains valid path then it override 
   previous values
3. `.config.override` in CWD
4. You can also set upper-cased env variable which matches one of those in 
   config

.. _faq_what_database:

What database can I use with solar ?
------------------------------------

By default for simplicity we use `sqlite`. On our vagrant environment we use
single node `riak`.
You can also use multiple nodes `riak`, with some strong consistent buckets.


Where can I find solar examples ?
---------------------------------

Example resources, composer templates and examples itself are located:
https://github.com/openstack/solar-resources
