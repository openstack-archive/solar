Usage:
Creating resources:

```
from x import resource
node1 = resource.create('node1', 'x/resources/ro_node/', 'rs/', {'ip':'10.0.0.3', 'ssh_key' : '/vagrant/tmp/keys/ssh_private', 'ssh_user':'vagrant'})

node2 = resource.create('node2', 'x/resources/ro_node/', 'rs/', {'ip':'10.0.0.4', 'ssh_key' : '/vagrant/tmp/keys/ssh_private', 'ssh_user':'vagrant'})

keystone_db_data = resource.create('mariadb_keystone_data', 'x/resources/data_container/', 'rs/', {'image' : 'mariadb', 'export_volumes' : ['/var/lib/mysql'], 'host': '', 'ssh_user': '', 'ssh_key': ''}, connections={'host' : 'node2.ip', 'ssh_key':'node2.ssh_key', 'ssh_user':'node2.ssh_user'})

nova_db_data = resource.create('mariadb_nova_data', 'x/resources/data_container/', 'rs/', {'image' : 'mariadb', 'export_volumes' : ['/var/lib/mysql'], 'host': '', 'ssh_user': '', 'ssh_key': ''}, connections={'host' : 'node1.ip', 'ssh_key':'node1.ssh_key', 'ssh_user':'node1.ssh_user'})
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
