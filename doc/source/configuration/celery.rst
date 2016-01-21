.. _celery:

Celery configuration
====================

Solar uses celery for messaging and task execution, in future release
it will be possible to use solar without celery and celery dependencies.

In solar config you can find 2 options related to celery ::

  celery_broker: sqla+sqlite:////tmp/celery.db
  celery_backend: db+sqlite:////tmp/celery.db

By default solar will use sqlite backend, therefore no changes will be required to start working with solar.
But if someone wants to expirement with other options it is possible
to use any supported `brokers <http://docs.celeryproject.org/en/latest/getting-started/brokers/>`_ and `backends <http://docs.celeryproject.org/en/latest/configuration.html#task-result-backend-settings/>`_.
