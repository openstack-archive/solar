Very simple solar example two nodes + hosts file mapping

Run:

`python examples/hosts_file/hosts.py`

Then you can continue with standard solar things:

```
solar changes stage -d
solar changes process
solar changes run-once last
watch -n 1 solar changes report last
```

Wait until all actions have state `SUCCESS`,
after that check `/etc/hosts` files on both nodes, it will contain entries like:

```
10.0.0.3 first1441705177.99
10.0.0.4 second1441705178.0
```

