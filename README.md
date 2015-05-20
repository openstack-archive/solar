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
* assign resources to nodes

```
# TODO Does not work without default values in golden templates
solar assign -n "env/test_env && node/1" -r resource/mariadb
```
