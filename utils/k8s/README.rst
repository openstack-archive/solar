Script for one-command deployment of k8s using `solar <https://github.com/openstack/solar>`_ and `solar-k8s by pigmej <https://github.com/pigmej/solar-k8s>`_.
=========================================================================================================================================================================

Deploying k8s cluster
---------------------
Run from main solar repo directory

``./utils/k8s/kube-up.sh``

WARNING:
If you have vagrant-gatling-rsync vagrant plugin installed, please ``^C`` the auto-rsync that happens after ``vagrant up``

After the script finishes, you can log in to k8s master and slave node with

``vagrant ssh solar-dev1``

``vagrant ssh solar-dev2``

Managing k8s cluster
--------------------
To manage your k8s cluster further (add nodes, enable dashboard etc.) please log in to solar dev node (``vagrant ssh``) and refer to `solar-k8s docs <https://github.com/pigmej/solar-k8s>`_. solar-k8s is cloned to ``/tmp/k8s`` by default.
