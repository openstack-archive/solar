
We should make network as separate resource for which we should be
able to add custom handlers.

This resource will actually serialize tasks, and provide inventory
information.


Input:

Different entities in custom database, like networks and nodes, maybe
interfaces and other things.

Another input is parameters, like ovs/linux (it may be parameters or
different tasks)

Output:


List of ansible tasks for orhestrator to execute, like

::

    shell: ovs-vsctl add-br {{networks.management.bridge}}

And data to inventory


Networking entities
-----------------------

Network can have a list of subnets that are attached to different node racks.

Each subnets stores l3 parameters, such as cidr/ip ranges.
L2 parameters such as vlans can be stored on network.

Roles should be attached to network, and different subnets can not
be used as different roles per rack.

How it should work:

1. Untagged network created with some l2 parameters like vlan
2. Created subnet for this network with params (10.0.0.0/24)
3. User attaches network to cluster with roles public/management/storage
4. Role can store l2 parameters also (bridge, mtu)
5. User creates rack and uses this subnet
6. IPs assigned for each node in this rack from each subnet
7. During deployment we are creating bridges based on roles.

URIs
-------

/networks/

vlan
mtu

/networks/<network_id>/subnets

cidr
ip ranges
gateway

/clusters/<cluster_id>/networks/

Subset of network attached to cluster

/clusters/<cluster_id>/networks/<network_id>/network_roles

Roles attached to particular network

/network_roles/

bridge

/clusters/<cluster_id>/racks/<rack_id>/subnets

/clusters/<cluster_id>/racks/<rack_id>/nodes



