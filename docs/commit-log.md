# Commit log analysis

See here https://files.slack.com/files-pri/T03ACD12T-F04V4QC6E/2015-05-21_16.14.50.jpg for details.

We have some data storage (to decide -- one global storage or separate storage for each resource?
One global commit log or separate for each resource?) -- call it DB for simplicity.

User modifies some data of some resources K1, K2, H. This data is not stored immediately in the DB,
instead it is stored in some separate place and queued for execution (we call this 'Staged Log').

The modified data for a resource is represented as a diff in its inputs. So if user adds new resource
and assigns an IP to it, it is represented something like:

```
ip:
  from: None
  to: 10.20.0.2
```

User commands 'apply'. Orchestrator takes the modified resources and applies appropriate actions
in appropriate order that it computes.

We think that the 'appropriate action' can be inferred from the diff for each resource. So for example
if resource is new and has added IP the action `run` can be inferred because previous state was
`None` and current is something new. If on the other hand previous state was some value `A` and
new state is some value `B` -- the orchestrator decides that the action to be run is `update`. And
if previous state is some `A` and new state is `None` the action will be `remove`.

The 'appropriate order' taken by orchestrator can be just like the data flow graph initially. We
see possibility of optimizing the number of actions taken by orchestrator so that moving Keystone
service to another node can be simplified from 4 actions (update HAProxy without removed Keystone,
install Keystone on new node, update HAProxy with new Keystone, remove Keystone from old node)
taken to 3 actions (add Keystone to new node, update HAProxy removing old Keystone and adding
new one, remove Keystone from old node).

After resource action is finished the new state is saved to the commit log and data is updated in
the DB.

We want to support rollbacks via commit log. Rollback is done by replaying the commit log backwards.

In case of separate commit logs per resource we think rollback could be done like this: some resource
`K` is rolled back by one commit log, the diff action is the same as reversed diff action of the
commit we are rolling back. We can update other resources with this new data by analyzing the connections.
So in other words -- we change the data in one resource according to what is in the commit to be rolled
back and then we trigger changes in other connected resources. Then we run orchestrator actions like
described above.

In case of single commit log for all resources -- is it sufficient to just rollback a commit? Or
do we need to trigger changes in connected resources too? In global commit log we have ordering
of commits like they were run by orchestrator.

From analysis of resource removal we think that we need to save connection data in each commit --
otherwise when we rollback that resource removal we wouldn't know how to restore its connections
to other resources.

Single commits after every action finished on a resource causes many commits per one user 'apply'
action. In order to allow user to revert the whole action and not just single commits we have some
idea of 'tagging' group of commits by some action id.
