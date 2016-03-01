Installation
============

Please note that currently Solar is in a beta stage and it shouldn't be used in
production environments.

We also recommend testing Solar using a vagrant where fully working development
environment will be created. Note that the vagrant-libvirt and vagrant-triggers
plugins are required for the vagrant libvirt provider.

If you want to try Solar outside Vagrant jump to `Local environment`_

Local environment
-----------------

If you want to test Solar locally you may install it via pip:

.. code-block:: bash

  pip install solar

Create solar configuration `solar_config` file and paste following data:

.. code-block:: yaml

  solar_db: sqlite:////tmp/solar.db

and set path to this configuration:

.. code-block:: bash

  export SOLAR_CONFIG_OVERRIDE=<full/path/solar_config>

For more information about configuration see our FAQ questions:
:ref:`here <faq_what_database>`.

You also need to download Solar resources and
add them to a Solar repository.

.. code-block:: bash

  git clone https://github.com/openstack/solar-resources

  sudo mkdir -p /var/lib/solar/repositories
  sudo chown -R <your_user_name> /var/lib/solar/

  solar repo import -l solar-resources/resources/
  solar repo import -l solar-resources/templates/

Next step is to start Solar orchestration worker.

.. code-block:: bash

  solar-worker
