Bootstraping lxc containers using solar and roles from os-ansible-deployment

At first run:

`python examples/lxc/example-lxc.py deploy`

It will do several things:

* Prepare about ~10 containers on solar-dev1
* Add linux bridge on solar-dev and solar-dev1 with uid br-int53
* Setup vxlan tunnel for solar-dev and solar-dev1
* Generate ssh key and inject it into containers

Later this containers can be used as regular nodes in solar.
Check rabbitmq example at the end of the file.

To deploy everything use usual solar commands.
```
solar changes stage -d
solar changes process
solar orch run-once last
watch -n 1 solar orch report last
```

Wait until all actions have state `SUCCESS`
