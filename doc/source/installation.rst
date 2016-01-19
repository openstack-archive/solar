Installation
============

Supported development platforms
-------------------------------

Linux or MacOS

Additional software
-------------------

`VirtualBox <https://www.virtualbox.org/wiki/Downloads/>`_ 5.x,
`Vagrant <http://www.vagrantup.com/downloads.html/>`_ 1.7.x

Note: Make sure that `Vagrant VirtualBox Guest plugin <https://github.com/dotless-de/vagrant-vbguest/>`_ is installed

.. code-block:: bash

  vagrant plugin install vagrant-vbguest

Note: If you are using VirtualBox 5.0 it's worth uncommenting paravirtprovider setting in `vagrant-settings.yaml` for speed improvements:

.. code-block:: bash

  paravirtprovider: kvm

For details see Customizing `vagrant-settings.yaml` section.

Setup development env
---------------------

Setup environment:

.. code-block:: bash

  cd solar
  vagrant up

Login into vm, the code is available in /vagrant directory

.. code-block:: bash

  vagrant ssh
  solar --help

Get ssh details for running slave nodes (vagrant/vagrant):

.. code-block:: bash

  vagrant ssh-config

You can make/restore snapshots of boxes (this is way faster than reprovisioning them)
with the `snapshotter.py` script:

.. code-block:: bash

  ./snapshotter.py take -n my-snapshot
  ./snapshotter.py show
  ./snapshotter.py restore -n my-snapshot

`snapshoter.py` to run requires python module `click`.

1. On debian based systems you can install it via `sudo aptitude install python-click-cli`,
2. On fedora 22 you can install it via `sudo dnf install python-click`,
3. If you use virtualenv or similar tool then you can install it just with `pip install click`,
4. If you don't have virtualenv and your operating system does not provide package for it then `sudo pip install click`.
5. If you don't have `pip` then [install it](https://pip.pypa.io/en/stable/installing/) and then execute command step 4.

Customizing vagrant-settings.yaml
---------------------------------

Solar is shipped with sane defaults in `vagrant-setting.yaml_defaults`. If you need to adjust them for your needs, e.g. changing resource allocation for VirtualBox machines, you should just compy the file to `vagrant-setting.yaml` and make your modifications.

Image based provisioning with Solar
-------------------------------------

* In `vagrant-setting.yaml_defaults` or `vagrant-settings.yaml` file uncomment `preprovisioned: false` line.
* Run `vagrant up`, it will take some time because it builds image for bootstrap and IBP images.
* Now you can run provisioning `/vagrant/solar-resources/examples/provisioning/provision.sh`
