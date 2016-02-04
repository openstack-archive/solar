.. _orchestration_entities:

Entities
========

Worker
------

Worker encapsulates logic related to certain area in solar.
Current we have next workers:

Scheduler
  Correctly initates execution plans and updates state of tasks.
Tasks
  Execute tasks scheduled by Scheduler worker
System log
  Updates system log e.g. commits and moves log item from staged log
  to history, or in case of error updates log item as erred

Executors
---------

Each executor module should provide:

Executor
  Executor responsible for processing events and handle them via given
  worker. Concurrency policies is up to the executor implementation.
Client
  Client communicates with executor

In current version of Solar we are using executor based on Push/Pull
zeromq sockets, and gevent pool for concurrent processing of events.

Subscriptions
-------------

Each public method of worker is subscribable, in current version
4 events are available to subscribers.

on_success
  Called in the case of successful execution, provides context, result
  and event arguments
on_error
  Called in the case of error, prorives context, error type, event
  arguments
before
  Called before method execution, provides only context
after
  Called after method executuon, provides only context

To subscribe use::

    worker.method.on_sucess(callable)

Additionally each worker provides *for_all* descriptor which allows
to subscribe to all public methods::

    worker.for_all.before(callable)
