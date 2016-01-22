Installation
============

Please note that currently Solar is in a beta stage and it shouldn't be used on
production.

We also recommend testing Solar in a vagrant env where fully working development
environment will be created.

If you want to try Solar outside Vagrant jump to `Local environment`_

Supported development platforms
-------------------------------

Linux or MacOS

Vagrant environment
-------------------

Additional software
~~~~~~~~~~~~~~~~~~~

`VirtualBox <https://www.virtualbox.org/wiki/Downloads/>`_ 5.x,
`Vagrant <http://www.vagrantup.com/downloads.html/>`_ 1.7.x

Note: Make sure that `Vagrant VirtualBox Guest plugin <https://github.com/dotless-de/vagrant-vbguest/>`_ is installed

.. code-block:: bash

  vagrant plugin install vagrant-vbguest

Note: If you are using VirtualBox 5.0 on Linux system, it's worth uncommenting paravirtprovider
setting in `vagrant-settings.yaml` for speed improvements:

.. code-block:: bash

  paravirtprovider: kvm

For details see `Customizing vagrant-settings.yaml`_ section.

Setup development env
~~~~~~~~~~~~~~~~~~~~~

Setup environment:

.. code-block:: bash

  git clone https://github.com/openstack/solar
  cd solar
  vagrant up

Login into vm, the code is available in /vagrant directory

.. code-block:: bash

  vagrant ssh
  solar --help

Get ssh details for running slave nodes (vagrant/vagrant):

.. code-block:: bash

  vagrant ssh-config

You can make/restore snapshots of boxes (this is way faster than reprovisioning
them)
with the `snapshotter.py` script:

.. code-block:: bash

  ./snapshotter.py take -n my-snapshot
  ./snapshotter.py show
  ./snapshotter.py restore -n my-snapshot

`snapshoter.py` to run requires python module `click`.

* On debian based systems you can install it via
 `sudo aptitude install python-click-cli`,
* On fedora 22 you can install it via `sudo dnf install python-click`,
* If you use virtualenv or similar tool then you can install it just with
 `pip install click`,
* If you don't have virtualenv and your operating system does not provide
 package for it then `sudo pip install click`.
* If you don't have `pip` then
 [install it](https://pip.pypa.io/en/stable/installing/) and then execute
 command step 4.

Customizing vagrant-settings.yaml
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Solar is shipped with sane defaults in `vagrant-setting.yaml_defaults`. If you
need to adjust them for your needs, e.g. changing resource allocation for
VirtualBox machines, you should just copy the file to `vagrant-setting.yaml`
and make your modifications.

Image based provisioning with Solar
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* In `vagrant-setting.yaml_defaults` or `vagrant-settings.yaml` file uncomment
  `preprovisioned: false` line.
* Run `vagrant up`, it will take some time because it builds image for
  bootstrap and IBP images.
* Now you can run provisioning
  `/vagrant/solar-resources/examples/provisioning/provision.sh`

Local environment
-----------------

If you want to test Solar locally you may install it via pip:

.. code-block:: bash

  pip install solar

You also need to download Solar resources and
add them to a Solar repository.

.. code-block:: bash

  git clone https://github.com/Mirantis/solar-resources

  sudo mkdir -p /var/lib/solar/repositories
  sudo chown -R <your_user_name> /var/lib/solar/

  solar repo import -l solar-resources/resources/
  solar repo import -l solar-resources/templates/

Next step is to start Solar orchestration worker.

.. code-block:: bash

  pip install gevent
  sudo mkdir -p /var/run/celery/
  sudo chown salmon -R /var/run/celery/
