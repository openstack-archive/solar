.. _orchestartion_configuration:

Configuration
=============

Orchestration is configured using two different methods.

1. Exposed config options
2. Setuptools entrypoints

Config options
--------------

* system_log_address (default: 'ipc:///tmp/solar_system_log')
  Passed to executor which will run system log worker
* tasks_address (default: 'ipc:///tmp/solar_tasks')
  Passed to executor which will run tasks worker
* scheduler_address (default: 'ipc:///tmp/solar_scheduler')
  Passed to executor which will run scheduler worker
* executor (default: 'zerorpc')
  Driver name should be registered in entrypoints
* tasks_driver (default: 'solar')
  Driver name should be registered in entrypoints
* scheduler_driver (default: 'solar')
  Driver name should be registered in entrypoints
* system_log_driver (default: 'solar')
  Driver name should be registered in entrypoints
* runner (defaut: 'gevent')
  Driver name should be registered in entrypoints

Entrypoints
-----------

* Drivers for executor namespace::
    solar.orchestration.executors

  One specified in configuration will be used.

* Extensions namespace::
    solar.orchestration.extensions

  Using driver namespaces for each worker - loads all workers.

* Worker driver namespaces::
    solar.orchestration.drivers.tasks
    solar.orchestration.drivers.scheduler
    solar.orchestration.drivers.system_log

  Only one driver can be selected from each namespace, see *_driver options
  in config.

* Constructor namespace::
    solar.orchestration.constructors

  Loads callables from this namespace and executes hooks connected
  to those namespaces.

* Constructor hooks namespaces::
    solar.orchestration.hooks.tasks.construct
    solar.orchestration.hooks.system_log.construct
    solar.orchestration.hooks.scheduler.construct

  All callables in each hook will be loaded and executed before spawning
  executor with instance of worker. Currently all subscriptions are done
  in this hooks.

* Runner namespace::
    solar.orchestration.runners

  Runner should be selected in solar config. Runner will be executed
  as a last step in solar-worker main function.
