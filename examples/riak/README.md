Example of 3 node riak cluster.

At first run:

`python examples/riak/riaks.py deploy`

It will prepare riak nodes etc.

Then you can continue with standard solar things:

```
solar changes stage -d
solar changes process
solar orch run-once last
watch -n 1 solar orch report last
```

Wait until all actions have state `SUCCESS`
After that you can add HAProxy on each node:

`python examples/riak/riaks.py add_haproxies`

Then again normal solar stuff

```
solar changes stage -d
solar changes process
solar orch run-once last
watch -n 1 solar orch report last
```


Wait until all actions have state `SUCCESS`
After that you have basic 3 node riak cluster running.

You can also modify riak http port by:

`solar resource update riak_service1 riak_port_http=18100`

And then again standard stuff:

```
solar changes stage -d
solar changes process
solar orch run-once last
watch -n 1 solar orch report last
```
