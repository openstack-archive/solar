.. _faq:


FAQ
===


.. _faq_hardcoded_params:

Why nodes/transports have hardcoded keys ip and other inputs ?
--------------------------------------------------------------

This is temporary situation, we will improve this situation in near future.

I want to use different keys
----------------------------

Just update resource for example::

    solar resource update ssh_transport1 '{"ssh_key": "/path/to/some/key"}'

I want to use passwords not keys
--------------------------------

Just update resource::

    solar resource update rsync1 '{"password": "vagrant", "key": null}'


How can I run solar celery worker ?
-----------------------------------

We created utils/celery-worker script. If you use `vagrant` then you can just `service solar-celery start|restart` as `vagrant` user.

.. note::

   We're currently working on removing celery completely.


How can I configure solar ?
---------------------------

There are several places where we search for config values:

1. `.config` file in CWD or in path from `SOLAR_CONFIG` env variable
2. if env `SOLAR_CONFIG_OVERRIDE` contains valid path then it override previous values
3. `.config.override` in CWD
4. You can also set upper-cased env variable which matches one of those in config


Why do you use celery with SQL backend instead of X ?
-----------------------------------------------------

For simplicity, but nothing stops you from changing these defaults::

  celery_broker: sqla+sqlite:////tmp/celery.db
  celery_backend: db+sqlite:////tmp/celery.db


What database can I use with solar ?
------------------------------------

By default for simplicity we use `sqlite`. On our vagrant environment we use single node `riak`.
You can also use multiple node `riak`, with some strong consistent buckets.


Where can I find solar examples ?
---------------------------------

Example resources, composer templates and examples itself are located: https://github.com/Mirantis/solar-resources
