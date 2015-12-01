Very simple solar example two nodes + hosts file mapping

Run:

`python examples/hosts_file/hosts.py`

Then you can continue with standard solar things:

```
solar changes stage -d
solar changes process
solar or run-once last
watch -n 1 solar or report last
```

Wait until all actions have state `SUCCESS`,
after that check `/etc/hosts` files on both nodes, it will contain entries like:

```
10.0.0.3 first1441705177.99
10.0.0.4 second1441705178.0
```

If you want to try out revert functionality - you can do it in a next way:

After you created all the stuff, print history like this:

`solar ch history`

Output:

```
log task=hosts_file1.run uid=282fe919-6059-4100-affc-56a2b3992d9d
log task=hosts_file2.run uid=774f5a49-00f1-4bae-8a77-90d1b2d54164
log task=node1.run uid=2559f22c-5aa9-4c05-91c6-b70884190a56
log task=node2.run uid=18f06abe-3e8d-4356-b172-128e1dded0e6
```

Now you can try to revert creation of hosts_file1

```
solar ch revert 282fe919-6059-4100-affc-56a2b3992d9d
solar ch stage
log task=hosts_file1.remove uid=1fe456c1-a847-4902-88bf-b7f2c5687d40
solar ch process
solar or run-once last
watch -n 1 solar or report last
```

For now this file will be simply cleaned (more cophisticated task can be added later).
And you can create revert of your revert, which will lead to created hosts_file1
resource and /etc/hosts with appropriate content

```
solar ch revert 282fe919-6059-4100-affc-56a2b3992d9d
solar ch stage
log task=hosts_file1.remove uid=1fe456c1-a847-4902-88bf-b7f2c5687d40
solar ch process
solar changes run-once last
watch -n 1 solar changes report last
```

After this you can revert your result of your previous revert, which will
create this file with relevant content.

```
solar ch history -n 1
log task=hosts_file1.remove uid=1fe456c1-a847-4902-88bf-b7f2c5687d40
solar ch revert 1fe456c1-a847-4902-88bf-b7f2c5687d40
solar ch stage
log task=hosts_file1.run uid=493326b2-989f-4b94-a22c-0bbd0fc5e755
solar ch process
solar changes run-once last
watch -n 1 solar changes report last
```

How to discard pending changes ?

After database was populated by some example, lets say
```
python examples/hosts_file/hosts.py deploy
```

User is able to discard all changes with
```
solar ch discard
```

Or any particular change with
```
solar ch stage
log task=hosts_file1.run uid=a5990538-c9c6-49e4-8d58-29fae9c7aaed
solar ch discard a5990538-c9c6-49e4-8d58-29fae9c7aaed
```

