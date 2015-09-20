# Problems to solve with removal operation

1. It is tricky to figure out what to do with data that will be left when
you are removing resource that is a parent for other resources.

The basic example is a node resource.
If hosts_file1 subscribed to node properties, and we will just remove
node - hosts_file1 will be left with corrupted data.
Validation is not a solution, because we can not expect user to remove
each resource one-by-one.

log task=hosts_file1.run uid=c1545041-a5c5-400e-8c46-ad52d871e6c3
    ++ ip: None
    ++ ssh_user: None
    ++ hosts: [{u'ip': None, u'name': u'riak_server1.solar'}]
    ++ ssh_key: None

Proposed solution:

Add `solar res remove node1 -r` where *r* stands for recursive.
During this operation we will find all childs of specified resource, and
stage them for removal as well.

2. If so we need to be able to determine what to do with child resource
on removal.
Basically this seems like another type of event:
hosts1.remove -> success -> node1.remove
And
hosts2.update -> success -> node2.remove
