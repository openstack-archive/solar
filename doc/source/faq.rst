.. _faq:


FAQ
===


.. _faq_hardcoded_params:

Why nodes/transports have hardcoded keys, ips and other inputs ?
--------------------------------------------------------------

This is temporary situation, we will improve it in near future.

.. _faq_different_ssh_keys:

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

There are several places where we search for config values:

1. `.config` file in CWD or in path from `SOLAR_CONFIG` env variable
2. if env `SOLAR_CONFIG_OVERRIDE` contains valid path then it override previous
values
3. `.config.override` in CWD
4. You can also set upper-cased env variable which matches one of those in
config

.. _faq_what_database:

What database can I use with solar ?
------------------------------------

By default for simplicity we use `sqlite`. On our vagrant environment we use
single node `riak`.
You can also use multiple nodes `riak`, with some strong consistent buckets.

.. _faq_solar_examples:

Where can I find solar examples ?
---------------------------------

Example resources, composer templates and examples itself are located:
https://github.com/openstack/solar-resources

.. _faq_solar_docker:

Can I run solar nodes with docker ?
-----------------------------------

Yes, although that is an experimental feature and currently supports only
a single network interface per a container. Note, that before to run the
``vagrant up --provider docker`` command, the following preparations must be
done at the host system:

.. code-block:: bash

  # docker pull solarproject/riak
  # git clone https://github.com/kiasaki/docker-alpine-postgres.git
  # cd docker-alpine-postgres
  # make build && cd -

This will allow the solar nodes to run required nested docker containers.

.. note ::
  The command ``vagrant ssh`` will not be working for the docker case.
  Instead, use any of the following commands (with a correct name/IP):

  .. code-block:: bash

    # ssh vagrant@10.0.0.2
    # docker exec -it solar-dev bash
