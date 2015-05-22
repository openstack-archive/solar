# x

## HAProxy deployment

```
cd /vagrant
python cli.py deploy haproxy_deployment/haproxy-deployment.yaml
```

or from Python shell:

```
from x import deployment

deployment.deploy('/vagrant/haproxy_deployment/haproxy-deployment.yaml')
```

## Usage:

Creating resources:

```
from x import resource

node1 = resource.create('node1', 'x/resources/ro_node/', 'rs/', {'ip':'10.0.0.3', 'ssh_key' : '/vagrant/tmp/keys/ssh_private', 'ssh_user':'vagrant'})

node2 = resource.create('node2', 'x/resources/ro_node/', 'rs/', {'ip':'10.0.0.4', 'ssh_key' : '/vagrant/tmp/keys/ssh_private', 'ssh_user':'vagrant'})

keystone_db_data = resource.create('mariadb_keystone_data', 'x/resources/data_container/', 'rs/', {'image' : 'mariadb', 'export_volumes' : ['/var/lib/mysql'], 'ip': '', 'ssh_user': '', 'ssh_key': ''}, connections={'ip' : 'node2.ip', 'ssh_key':'node2.ssh_key', 'ssh_user':'node2.ssh_user'})

nova_db_data = resource.create('mariadb_nova_data', 'x/resources/data_container/', 'rs/', {'image' : 'mariadb', 'export_volumes' : ['/var/lib/mysql'], 'ip': '', 'ssh_user': '', 'ssh_key': ''}, connections={'ip' : 'node1.ip', 'ssh_key':'node1.ssh_key', 'ssh_user':'node1.ssh_user'})
```

to make connection after resource is created use `signal.connect`

To test notifications:

```
keystone_db_data.args    # displays node2 IP

node2.update({'ip': '10.0.0.5'})

keystone_db_data.args   # updated IP
```

If you close the Python shell you can load the resources like this:

```
from x import resource

node1 = resource.load('rs/node1')

node2 = resource.load('rs/node2')

keystone_db_data = resource.load('rs/mariadn_keystone_data')

nova_db_data = resource.load('rs/mariadb_nova_data')
```

Connections are loaded automatically.


You can also load all resources at once:

```
from x import resource

all_resources = resource.load_all('rs')
```

## CLI

You can do the above from the command-line client:

```
cd /vagrant

python cli.py resource create node1 x/resources/ro_node/ rs/ '{"ip":"10.0.0.3", "ssh_key" : "/vagrant/tmp/keys/ssh_private", "ssh_user":"vagrant"}'

python cli.py resource create node2 x/resources/ro_node/ rs/ '{"ip":"10.0.0.4", "ssh_key" : "/vagrant/tmp/keys/ssh_private", "ssh_user":"vagrant"}'

python cli.py resource create mariadb_keystone_data x/resources/data_container/ rs/ '{"image": "mariadb", "export_volumes" : ["/var/lib/mysql"], "ip": "", "ssh_user": "", "ssh_key": ""}'

python cli.py resource create mariadb_nova_data x/resources/data_container/ rs/ '{"image" : "mariadb", "export_volumes" : ["/var/lib/mysql"], "ip": "", "ssh_user": "", "ssh_key": ""}'

# View resources
python cli.py resource show rs/mariadb_keystone_data

# Show all resources at location rs/
python cli.py resource show rs/ --all

# Show resources with specific tag
python cli.py resources show rs/ --tag test

# Connect resources
python cli.py connect rs/node2 rs/mariadb_keystone_data

python cli.py connect rs/node1 rs/mariadb_nova_data

# Test update
python cli.py update rs/node2 '{"ip": "1.1.1.1"}'
python cli.py resource show rs/mariadb_keystone_data  # --> IP is 1.1.1.1

# View connections
python cli.py connections show

# Outputs graph to 'graph.png' file, please note that arrows don't have "normal" pointers, but just the line is thicker
# please see http://networkx.lanl.gov/_modules/networkx/drawing/nx_pylab.html
python cli.py connections graph

# Disconnect
python cli.py disconnect rs/mariadb_nova_data rs/node1

# Tag a resource:
python cli.py resource tag rs/node1 test-tag
# Remove tag
python cli.py resource tag rs/node1 test-tag --delete
```
