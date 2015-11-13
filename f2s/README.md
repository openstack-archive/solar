#How to install on fuel master?

To use solar on fuel master we need to use container because of
python2.6 there. Also solar itself relies on several services.

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

#f2s.py

This script converts tasks.yaml + library actions into solar resources,
vrs, and events.

1. Based on tasks.yaml meta.yaml is generated, you can take a look on example
at f2s/resources/netconfig/meta.yaml
2. Based on hiera lookup we generated inputs for each resource, patches can be
found at f2s/patches
3. VRs (f2s/vrs) generated based on dependencies between tasks and roles

#fsclient.py

This script helps to create solar resource with some of nailgun data

`./f2s/fsclient.py master 1`
Accepts cluster id, prepares transports for master + generate keys task
for current cluster.

`./f2s/fsclient.py nodes 1`
Prepares transports for provided nodes, ip and cluster id fetchd from nailgun.

`./f2s/fsclient.py prep 1`
Creates tasks for syncing keys + fuel-library modules.

`./f2s/fsclient.py roles 1`
Based on roles stored in nailgun we will assign vrs/<role>.yaml to a given
node. Right now it takes while, so be patient.

#fetching data from nailgun

Special entity added which allows to fetch data from any source
*before* any actual deployment.
This entity provides mechanism to specify *manager* for resource (or list of them).
Manager accepts inputs as json in stdin, and outputs result in stdout,
with result of manager execution we will update solar storage.

Examples can be found at f2s/resources/role_data/managers.

Data will be fetched on solar command

`solar res prefetch -n <resource name>`

#tweaks

Several things needs to be manually adjusted before you can use solar
on fuel master.

- provision a node by fuel
  `fuel node --node 1 --provision`
- create /var/lib/astute directory on remote
- install repos using fuel
  `fuel node --node 1 --tasks core_repos`
- configure hiera on remote, and create /etc/puppet/hieradata directory
```
 :backends:
  - yaml
  #- json
:yaml:
  :datadir: /etc/puppet/hieradata
:json:
  :datadir: /etc/puppet/hieradata
:hierarchy:
  - "%{resource_name}"
  - resource
```

All of this things will be automated by solar eventually
