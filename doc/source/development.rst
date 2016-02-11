Developement environment
=================================

Vagrant environment
-------------------

Currently for development we are using Vagrant.

Additional software
~~~~~~~~~~~~~~~~~~~

`VirtualBox <https://www.virtualbox.org/wiki/Downloads/>`_ 5.x,
or `Libvirt <https://libvirt.org/>`_
`Vagrant <http://www.vagrantup.com/downloads.html/>`_ 1.7.4 or higher

Note: Make sure that `Vagrant VirtualBox Guest plugin
<https://github.com/dotless-de/vagrant-vbguest/>`_ is installed

.. code-block:: bash

  vagrant plugin install vagrant-vbguest

Note: If you are using VirtualBox 5.0 on Linux system, it's worth uncommenting
paravirtprovider setting in `vagrant-settings.yaml` for speed improvements:

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

To develop Solar we use Vagrant

Using Libvirt instead of Virtualbox
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Virtualbox is a default provider for Vagrant, but it's also possible to use
another providers. It should be possible to use any of Vagrant providers. As
for today we support Libvirt provider. It can be used only on Linux systems.

To use Libvirt with vagrant just run:

.. code-block:: bash

  vagrant up --provider libvirt

This will download libvirt image for vagrant.

In nodes definition we have hardcoded ssh keys paths, where we assume that
Virtualbox is used. You need to copy keys to vagrant libvirt dir:

.. code-block:: bash

  cp /vagrant/.vagrant/machines/solar-dev1/libvirt/private_key /vagrant/.vagrant/machines/solar-dev1/virtualbox/private_key

do it for each solar-dev* machine.

.. note::

  Libvirt be default is using KVM. You cannot run KVM and Virtualbox
  at the same time.


Contribution
------------

To track development process we are using Launchpad. To see on what we are
currently working check `Series and milestones <https://launchpad.net/solar>`_.

Submiting patches
~~~~~~~~~~~~~~~~~

We are using OpenStack infrastructure to track code changes which is using
Gerrit. To see all proposed changes go to `Solar panel <https://review.openstack.org/#/q/project:openstack/solar>`_

Reporting bugs
~~~~~~~~~~~~~~

To trach bugs we are using Launchpad. You can see all Solar bugs
`here <https://bugs.launchpad.net/solar>`_
