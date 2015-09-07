# Example script that uses the "compiled resources" functionality

To run this code, first compile the resources with

```bash
solar resource compile_all
```

Please note that you don't have to anymore write

```python
node1 = resource.create('node1', 'resources/ro_node/', {'ip': '10.0.0.3', 'ssh_key': '/vagrant/.vagrant/machines/solar-dev1/virtualbox/private_key', 'ssh_user': 'vagrant'})
```

but instead you can do:
```python
import resources_compiled

node1 = resources_compiled.RoNodeResource('node1', None, {})
node1.ip = '10.0.0.3'
node1.ssh_key = '/vagrant/.vagrant/machines/solar-dev1/virtualbox/private_key'
node1.ssh_user = 'vagrant'
```

Resources aren't anymore a collection of dicts with inputs that are hard to
trace, but they are full Python classes for which you can use your IDE's
autocompletion, etc. functionality.
