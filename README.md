# Setup development env
* Install virtualbox
* Install vagrant
* Setup environment

```
$ cd fuel-ng
$ vagrant up
```

* Login into vm, the code is available in /vagrant directory

```
$ vagrant ssh
$ solar --help
```

## Solar usage
* discover nodes, with standard file based discovery

```
solar discover
```

* create profile (global config)

```
solar profile --create --id prf1 --tags env/test_env

```
* assign nodes to profile with tags


* edit nodes files, in the future we want to provide
  some cli in order to change the data

```
vim tmp/storage/nodes-id.yaml
```

* add `env/test_env` in tags list
* in order to assign resouce to the node use the same the same
  method, i.e. add in tags list for node your service e.g.
  `service/docker`, `service/mariadb`
* perform deployment

```
solar configure --profile prf1 -pa run
```
