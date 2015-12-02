Running Fuel tasks in Solar
===========================

Workflow
---------

1. Deploy Fuel master node
2. Provision nodes `fuel node --node 1,2,3 --provision`
3. Create `/var/lib/astute directory` on nodes
4. Run upload_core_repos task `fuel node --node 1,2,3 --tasks upload_core_repos`
5. Configure `/etc/puppet/hiera.yaml` and create `/etc/puppet/hieradata` directory on slaves
```
:backends:
  - yaml
:yaml:
  :datadir: /etc/puppet/hieradata
:json:
  :datadir: /etc/puppet/hieradata
:hierarchy:
  - "%{resource_name}"
  - resource
```
6. Distribute keys and certs
```
scp /var/lib/astute/ceph/ceph* root@node-1:/var/lib/astute/ceph/

sh /etc/puppet/modules/osnailyfacter/modular/astute/generate_haproxy_keys.sh -i 1 -h public.fuel.local -o 'haproxy' -p /var/lib/fuel/keys/
scp /var/lib/fuel/keys/1/haproxy/public_haproxy.pem root@node-1:/var/lib/astute/haproxy/public_haproxy.pem
scp /var/lib/fuel/keys/1/haproxy/public_haproxy.crt root@node-1:/etc/pki/tls/certs/public_haproxy.pem
```

7. To use solar on Fuel master we need to use containers because of python2.6 there. Also Solar by itself relies on several services.
```
yum -y install git

git clone -b f2s https://github.com/Mirantis/solar.git

docker run --name riak -d -p 8087:8087 -p 8098:8098 tutum/riak

docker run --name redis -d -p 6379:6379 -e REDIS_PASS=**None** tutum/redis

docker run --name solar -d -v /root/solar/solar:/solar -v /root/solar/solard:/solard -v /root/solar/templates:/templates \
-v /root/solar/resources:/resources -v /root/solar/f2s:/f2s \
-v /var/lib/fuel:/var/lib/fuel -v /root/.config/fuel/fuel_client.yaml:/etc/fuel/client/config.yaml -v /etc/puppet/modules:/etc/puppet/modules \
-v /root/.ssh:/root/.ssh \
--link=riak:riak --link=redis:redis solarproject/solar-celery:f2s
```
8. Go inside the solar container
`
docker exec -ti solar bash
`
9. Prepare transport for master and nodes, generate keys, create tasks and assign virtual resources to nodes.
```
./f2s/fsclient.py master 1

./f2s/fsclient.py nodes 1 2 3

./f2s/fsclient.py prep 1 2 3

./f2s/fsclient.py roles 1 2 3
```
10. Update resource inputs from nailgun for all nodes
`
solar res prefetch -n role_data1
`
11. Create deployment scenario
`
solar ch stage && solar ch process
`
12. Run Solar deployment
`
solar or run-once last
`
13. Enjoy deployment, you can check status using
`
solar o report
`

fsclient.py
-----------

This script helps to create solar resources with data from nailgun.
Note, you should run it inside of the solar container.

`./f2s/fsclient.py master 1`
Accepts cluster id, prepares transports for master + generate keys task
for current cluster.

`./f2s/fsclient.py nodes 1`
Prepares transports for provided nodes, ip and cluster id fetchd from nailgun.

`./f2s/fsclient.py prep 1`
Creates tasks for syncing keys + fuel-library modules.

`./f2s/fsclient.py roles 1`
Based on roles stored in nailgun it will assign vrs/<role>.yaml to a given
node. Right now it takes time, so please be patient.

Fetching data from nailgun
--------------------------

Special entity which allows to fetch data from any source *before* any actual deployment.
This entity provides mechanism to specify *manager* for resources (or list them).
Manager accepts inputs as json in stdin, and outputs result in stdout,
with result of manager execution we are updating solar storage.

Examples can be found at f2s/resources/role_data/managers.
Data can be fetched by solar command

`solar res prefetch -n <resource name>`

Troubleshooting
---------------

- To regenerate the deployment data run
`
solar res clear_all
`
and repeat all fsclient.py tasks and fetching from nailgun data steps.

 - To skip any resources you should mark them using
`
solar or noop last -t ironic-api5.run
`

 - To retry all failed resources and proceed
`
solar or retry last
`

 - If you see any strange SSH/transport errors in solar report run

`
ansible-playbook -v -i "localhost," -c local /celery.yaml --skip-tags slave
`

 - You can run particular resource by
`
solar res action run openstack-haproxy-ironic5
`

 - Deployment can be debugged using
`
tail -f /var/run/celery/celery2.log
`

 - If there are any Fuel plugin installed, you should manually
create a stanza for it in the `./f2s/resources/role_data/meta.yaml`,
like below and regenerate the data from nailgun:
```
input:
  foo_plugin_name:
    value: null
```
