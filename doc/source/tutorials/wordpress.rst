Wordpress tutorial
==================

1. Introduction
---------------
In this tutorial we will create Worpdress site using docker containers. We will create one container with Mysql database, then we will create database and user for it. After that we will create Wordpress container which is running Apache.

For now you can use Solar only in our Vagrant environment.  
First checkout Solar repo and start vagrant. We need two virtual machines. One where Solar database and Orchestrator will run and one where we will install Wordpress and all components:

2. Solar installation
---------------------

.. code-block:: bash

   git clone https://github.com/openstack/solar.git
   cd solar
   vagrant up solar-dev solar-dev1
   vagrant ssh solar-dev
   cd /vagrant

.. note::
   For now please assume that all `solar` commands are run from dir `/vagrant`

3. Config resource
------------------

First we need to create Solar Resource definition where global configuration will be stored. This will be a `data container` only, so it will not have any handler nor actions. Let's create base structure:

.. code-block:: bash

  mkdir /vagrant/tmp/wp_config
  touch /vagrant/tmp/wp_config/meta.yaml

Open meta file `/vagrant/tmp/wp_config/meta.yaml` with your favorite text editor and paste the following data:

.. code-block:: yaml
  
  id: container
  handler: none
  version: 1.0.0
  input:
    db_root_pass:
      schema: str!
      value:
    db_port:
      schema: int!
      value:
    wp_db_name:
      schema: str!
      value:
    wp_db_user:
      schema: str!
      value:
    wp_db_pass:
      schema: str!
      value:

Let's go through this document line by line. `id:container` is not used currently and may be removed in future. `handler: none` says that this resource has no handler and no actions. In next line we define version. Currently it's also not used. The most important part starts from line 4. We define there the inputs for this resource. It will be possible to configure following inputs: 

* `db_root_pass` - Mysql root password
* `db_port` - Mysql port
* `wp_db_name` - database name for Wordpress
* `wp_db_user` - database user name for Wordpress
* `wp_db_pass` - database user password for Wordpress

In schema it's defined if input will be string or integer, `!` at the end means that the input is mandatory and can not be empty.

4. Virtual resource
-------------------

All other required resources are already available in solar repo in `resources` dir. We will use four more resources:

* resources/docker - it installs docker 
* resources/docker_container - it manages docker container
* resources/mariadb_db - it creates database in MariaDB and Mysql
* resources/mariadb_user - it creates user in MariaDB and Mysql

There are three ways to create resources in Solar: Python API, CLI and Virtual Resources. We will use the last option. 
Virtual Resource is just a simple yaml file where we define all needed resources and connections.

Create new file `docker.yaml` in /vagrant dir, open it and past the following data:

.. code-block:: yaml

  resources:
    - id: docker
      from: resources/docker
      location: node1

    - id: config
      from: tmp/wp_config
      location: node1
      values:
        db_root_pass: 'r00tme'
        db_port: 3306
        wp_db_name: 'wp'
        wp_db_user: 'wp'
        wp_db_pass: 'h4ack'
      
    - id: mysql
      from: resources/docker_container
      location: node1
      values:
        ip: node1::ip
        image: mysql:latest
        ports:
          - config::db_port
        env:
          MYSQL_ROOT_PASSWORD: config::db_root_pass

    - id: wp_db
      from: resources/mariadb_db
      location: node1
      values:
        db_name: config::wp_db_name
        db_host: mysql::ip
        login_user: 'root'
        login_password: config::db_root_pass
        login_port: config::db_port

    - id: wp_user
      from: resources/mariadb_user
      location: node1
      values:
        user_password: config::wp_db_pass
        user_name: config::wp_db_user
        db_name: wp_db::db_name
        db_host: mysql::ip
        login_user: 'root'
        login_password: config::db_root_pass
        login_port: config::db_port

    - id: wordpress
      from: resources/docker_container
      location: node1
      values:
        ip: node1::ip
        image: wordpress:latest
        env:
          WORDPRESS_DB_HOST: mysql::ip
          WORDPRESS_DB_USER: wp_user::user_name
          WORDPRESS_DB_PASSWORD: wp_user::user_password
          WORDPRESS_DB_NAME: wp_db::db_name

In block `resources` we define... resources. Each section is one resource. Each resource definition has a following structure:

* id - resource name
* from - path to resource dir
* location - node where resource will be run
* values: initialization of a Resource Inputs

As you can see entries for `from` have relative paths. For now we do not have any resource repository. This is why it's safer to run all commands from /vagrant dir. In `location` we define `node1`. It's name of our virtual machine resource. It's not created yet, we will do it shortly.

In our configuration there are two formats which we use to assign values to inputs. First:

.. code-block:: yaml

  db_port: 3306

It just means that input `db_port` will be set to `3306`

Another format is:

.. code-block:: yaml

  login_port: config::db_port

This means that input `login_port` will have the same value as input `db_port` from resource `config`. In Solar we call it Connection. Now when value of `db_port` changes, value of `login_port` will also change.


5. Deploying
------------

Now it's time to deploy our configuration. When running `vagrant up solar-dev solar-dev1` you started two virtual machines. We will deploy Wordpress on solar-dev1. To do it we need to create a resource for it. We already have in repo virtual resource which is doing it. Just run:

.. code-block:: bash

  solar resource create nodes templates/nodes.yaml count=1

It will create all required resources to run actions on solar-dev1. You can analyze `templates/nodes.yaml` later. Now we create resources defined in `docker.yaml`

.. code-block:: bash

  solar resource create docker docker.yaml

Command `create` requires name, but it's not used for VirtualResources.

Now you can deploy all changes with:

.. code-block:: bash

  solar changes stage
  solar changes process
  solar orch run-once

To see deployment progress run:

.. code-block:: bash

  solar orch report

Wait until all task will return status `SUCCESS`. When it's done you should be able to open Wordpress site at http://10.0.0.3

6. Update
---------

Now change password for Wordpress database user

.. code-block:: bash

  solar resource update config wp_db_pass=new_hacky_pass

and deploy new changes

.. code-block:: bash

  solar changes stage
  solar changes process
  solar orch run-once

Using `report` command wait until all tasks finish. Wordpress should still working and new password should be used.
