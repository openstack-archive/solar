# Setup development env

* Install vagrant
* Setup environment:
```
cd solar
vagrant up
```

* Login into vm, the code is available in /vagrant directory
```
vagrant ssh
solar --help
```

* Launch standard deployment:
```
python example.py
```

## Solar usage

* To clear all resources/connections:
```
solar resource clear_all
solar connections clear_all
```

* Some very simple cluster setup:
```
cd /vagrant

solar resource create node1 resources/ro_node/ '{"ip":"10.0.0.3", "ssh_key" : "/vagrant/.vagrant/machines/solar-dev1/virtualbox/private_key", "ssh_user":"vagrant"}'
solar resource create mariadb_service resources/mariadb_service '{"image": "mariadb", "root_password": "mariadb", "port": 3306}'
solar resource create keystone_db resources/mariadb_keystone_db/ '{"db_name": "keystone_db", "login_user": "root"}'
solar resource create keystone_db_user resources/mariadb_user/ '{"user_name": "keystone", "user_password": "keystone", "login_user": "root"}'

solar connect node1 mariadb_service
solar connect node1 keystone_db
solar connect mariadb_service keystone_db --mapping '{"root_password": "login_password", "port": "login_port"}'
solar connect mariadb_service keystone_db_user --mapping '{"root_password": "login_password", "port": "login_port"}'
solar connect keystone_db keystone_db_user

solar changes stage
solar changes commit
```

You can fiddle with the above configuration like this:
```
solar resource update keystone_db_user '{"user_password": "new_keystone_password"}'

solar changes stage
solar changes commit
```

* Show the connections/graph:
```
solar connections show
solar connections graph
```

# Low level API

## HAProxy deployment (not maintained)

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

# View resourcespython cli.py resource show rs/mariadb_keystone_data
# Show all resources at location rs/
python cli.py resource show rs/ --all

# Show resources with specific tagspython cli.py resources show rs/ --tag test

# Connect resourcespython cli.py connect rs/node2 rs/mariadb_keystone_data
python cli.py connect rs/node1 rs/mariadb_nova_data
# Test updatepython cli.py update rs/node2 '{"ip": "1.1.1.1"}'
python cli.py resource show rs/mariadb_keystone_data  # --> IP is 1.1.1.1

# View connections
python cli.py connections show

# Outputs graph to 'graph.png' file, please note that arrows don't have "normal" pointers, but just the line is thicker
# please see http://networkx.lanl.gov/_modules/networkx/drawing/nx_pylab.html
python cli.py connections graph

# Disconnect
python cli.py disconnect rs/mariadb_nova_data rs/node1

# Tag a resource:
python cli.py resource tag rs/node1 test-tags# Remove tagspython cli.py resource tag rs/node1 test-tag --delete
```
