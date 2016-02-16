.. _orchestartion_configuration:

Configuration
=============

Orchestration is configured using two different methods.

1. :ref:`orchestration_config`
2. :ref:`orchestration_entrypoints`

.. _orchestration_config:

Config options
--------------

system_log_address
^^^^^^^^^^^^^^^^^^
Passed to executor which will run system log worker

tasks_address
^^^^^^^^^^^^^
Passed to executor which will run tasks worker

scheduler_address
^^^^^^^^^^^^^^^^^
Passed to executor which will run scheduler worker

executor
^^^^^^^^
Driver name should be registered in entrypoints, see :ref:`namespace_executors`

tasks_driver
^^^^^^^^^^^^
Driver name should be registered in appropriate entrypoints
(see :ref:`namespace_workers`)

scheduler_driver
^^^^^^^^^^^^^^^^
Driver name should be registered in appropriate entrypoints
(see :ref:`namespace_workers`)

system_log_driver
^^^^^^^^^^^^^^^^^
Driver name should be registered in appropriate entrypoints
(see :ref:`namespace_workers`)

runner
^^^^^^
Driver name should be registered in entrypoints (see :ref:`namespace_runner`)

.. _orchestration_entrypoints:

Entrypoints
-----------

.. _namespace_executors:

Executor namespace
^^^^^^^^^^^^^^^^^^
.. note::
    solar.orchestration.executors

One specified in configuration will be used.

.. _namespace_extensions:

Extensions namespace
^^^^^^^^^^^^^^^^^^^^
.. note::
    solar.orchestration.extensions

Using driver namespaces for each worker - loads all workers.

.. _namespace_workers:

Worker driver namespaces
^^^^^^^^^^^^^^^^^^^^^^^^
.. note::
    | solar.orchestration.drivers.tasks
    | solar.orchestration.drivers.scheduler
    | solar.orchestration.drivers.system_log

Only one driver can be selected from each namespace, see driver options
in config.

.. _namespace_constructor:

Constructor namespace
^^^^^^^^^^^^^^^^^^^^^
.. note::
    solar.orchestration.constructors

Loads callables from this namespace and executes hooks connected
to those namespaces.

.. _namespace_contructor_hooks:

Constructor hooks namespaces
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. note::
    | solar.orchestration.hooks.tasks.construct
    | solar.orchestration.hooks.system_log.construct
    | solar.orchestration.hooks.scheduler.construct

All callables in each hook will be loaded and executed before spawning
executor with instance of worker. Currently all subscriptions are done
in this hooks.

.. _namespace_runner:

Runner namespace
^^^^^^^^^^^^^^^^
.. note::
    solar.orchestration.runners

Runner should be selected in solar config. Runner will be executed
as a last step in solar-worker main function.
