[DRAFT] events propagation

Possible events on a resource:

1. changed
configuration management executed on resource, and changes were found,
both ansible and puppet is able to know if there were any changes

2. failed, error
error - corresponds to problems in infrastructure, and probably cant be remediated in any way
failed - process of configuring resource failed
Does it make sense to create such separation?

3. ok
Resource executed without errors or changes, so successors may skip reloading
or whatever

4. created ??
is there such cases when we need to differentiate between updated object
and created?

--------------------------------------------------
Propagating events when there is no data changed

Control for specifying events:

on <emitter>.<emmiter_action> <event> <subscriber>.<subsciber_action>

on mariadb.run                changed keystone.run
on keystone.run               changed keystone_config.run
on keystone_config.run        changed haproxy.reload

+---------------------+
|     mariadb.run     |
+---------------------+
  |
  | changed
  v
+---------------------+
| keystone_config.run |
+---------------------+
  |
  | changed
  v
+---------------------+
|   haproxy.reload    |
+---------------------+

<u>.<action> - <event> - <v>.<action>

When data connection between several resources created - events connections should
be created as well, resource a connect resource b:

on a.run    changed b.reload
on a.remove changed b.run

-------------------------------------------------
Resolving cycles on a data plane

Resolving rmq cycle with events, lets say we have 4 objects:
- rmq.cluster
- rmq.1, rmq.2, rmq.3

rmq.cluster is a sinc that will use data from all 3 nodes, and those nodes will
consume that sinc - so there is a cycle. We can not depend just on data to resolve
this cycle.

Order of execution should be like this:

rmq.1.run rmq.2.run rmq.3.run
rmq.1.cluster_create
rmq.2.cluster_join, rmq.2.cluster_join

Also cluster operation should happen only when rmq.cluster is changed.

on rmq.cluster          changed rmq.1.cluster_create
on rmq.1.cluster_create changed rmq.2.cluster_join
on rmq.1.cluster_create changed rmq.3.cluster_join

+----------------------+
|      rmq.1.run       |
+----------------------+
  |
  | changed
  v
+----------------------+
| rmq.1.cluster_create | -+
+----------------------+  |
  |                       |
  | changed               |
  v                       |
+----------------------+  |
|  rmq.2.cluster_join  |  |
+----------------------+  |
  ^                       |
  | changed               | changed
  |                       |
+----------------------+  |
|      rmq.2.run       |  |
+----------------------+  |
+----------------------+  |
|      rmq.3.run       |  |
+----------------------+  |
  |                       |
  | changed               |
  v                       |
+----------------------+  |
|  rmq.3.cluster_join  | <+
+----------------------+



---------------------------------------------------
Resolve cycles on a execution level

We have 5 objects, which forms 2 pathes
- keystone-config -> keystone-service -> haproxy-sevice
- glance-config -> glance-service -> haproxy-service

But also we have keystone endpoint exposed via haproxy, and it is consumed in
glance-config, therefore there is a cycle. And proper resolution for this
cycle would be to install haproxy after keystone is configured, and after that
configure glance, and only after reload haproxy one more time to ensure that
glance exposed via haproxy.

     +----+
     | g  |
     +----+
       |
       |
       v
     +----+
     | gc | <+
     +----+  |
       |     |
       |     |
       v     |
     +----+  |
  +> | ha | -+
  |  +----+
  |  +----+
  |  | k  |
  |  +----+
  |    |
  |    |
  |    v
  |  +----+
  +- | kc |
     +----+

During traversal we should check if added node forms a cycle, find a pair
of nodes that created this cycle and create a node with incremented action.
In the above example this resolution will help if ha.run will be incremented
and we will have two actions - ha.run#0 and ha.run#1, and gc.run#0 will lead
to ha.run#1.
