Deploying simple two node OpenStack env.

You need to run it from main solar directory. To prepare resources run:

`python examples/openstack/openstack.py create_all`

Then to start deployment:

`solar changes stage
solar changes process
solar orch run-once last`

To see the progress:

`solar orch report`
