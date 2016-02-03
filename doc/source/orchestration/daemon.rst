.. _orchestration_daemon:

Daemonizing solar-worker
========================

.. _orchestration_daemon_upstart:

Upstart
-------

To daemonize solar-worker on debian or ubuntu `upstart script`_ should be used,
in script and pre-script stanzas - */etc/default/solar-worker* will be sourced, and following variables used::

    SOLAR_UID=solar
    SOLAR_GID=solar
    SOLAR_PIDFILE=/var/opt/solar/solar-worker.pid

.. warning::
    SOLAR_UID and SOLAR_GID should be present in the system.

.. _upstart script: https://github.com/openstack/solar/blob/master/utils/solar-worker.conf


