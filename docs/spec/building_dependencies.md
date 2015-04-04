

Problem: Different execution strategies
---------------------------------------

We will have different order of execution for different actions
(installation, removal, maintenance)

1. Installation and removal of resources should be done in different order.
2. Running maintenance tasks may require completely different order
of actions, and this order can not be described one time for resources,
it should be described for each action.

IMPORTANT: In such case resources are making very little sense,
because we need to define different dependencies and build different
executions graphs for tasks during lifecycle management


Dependency between resources
-----------------------------
Several options to manage ordering between executables

1. Allow user to specify this order
2. Explicitly set requires/require_for in additional entity like profile
3. Deployment flow should reflect data-dependencies between resources

1st option is pretty clear - and we should provide a way for user
to manage dependencies by himself
(even if they will lead to error during execution)

2nd is similar to what is done in fuel, and allows explicitly set
what is expected to be executed. However we should
not hardcode those deps on resources/actions itself. Because it will lead to
tight-coupling, and some workarounds to skip unwanted resource execution.

3rd option is manage dependencies based on what is provided by different
resources. For example input: some_service

Please note that this format is used only to describe intentions.

::
    image:
        ref:
          namespace: docker
          value: base_image

Practically it means that docker resource should be executed before
some_service. And if another_service needs to be connected to some_service

::
    connect:
        ref:
            namespace: some_service
            value: port

But what if there is no data-dependencies?

In such case we can add generic way to extend parameters with its
requirements, like:

::

    requires:
        - ref:
            namespace: node

# (dshulyak) How to add backward dependency? (required_for)
