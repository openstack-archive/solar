.. _tutorial_dev:

Development tutorial
====================

1. Introduction
---------------

After getting your feet wet in :ref:`tutorial_wordpress`
let's try deploying a simple python application with Solar.
We will create our own handlers here.
We will use the same :ref:`development_environment`
that we used in Wordpress tutorial.

2. Installing PostgreSQL
------------------------

Although puppet has a plugin
that facilitates database and plugin creation,
we won't use it in solar,
as it doesn't allow us to take back all our changes.
Instead we will perform the installation of PostgreSQL service
using normal puppet ``package`` and ``service`` resources.

First create postgres repository:

.. code-block:: bash

    mkdir -p postgres_repo/postgresql/1.0.0/actions

Now open ``postgres_repo/postgresql/1.0.0/meta.yaml``
with your favourite editor.

.. code-block:: yaml

    handler: puppet
    input: {}

This is an ultra-simple meta-file,
as we will depend on default settings
apt will configure for us.
Now open ``postgres_repo/postgresql/1.0.0/actions/run.pp``

.. code-block:: puppet

    package { 'postgresql-common':
        ensure => present,
    }

    package { 'postgresql-9.3':
        ensure => present,
    }

    package { 'postgresql-client-common':
        ensure => present,
    }

    package { 'libpq-dev':
        ensure => present,
    }

The manifests for ``update`` and ``remove`` actions will be very similar.

.. code-block:: bash

    $ cd postgres_repo/postgresql/1.0.0/actions
    $ cp run.pp update.pp
    $ sed -e 's/present/absent/' run.pp > remove.pp

3. SQL handler
-------------------------------

Let's now do something more challenging
and create our own handler.
This handler would be similar to the puppet one
in that it would be based
on a set of action files executed on the node.
Instead of puppet manifests we will use SQL files however.

Solar uses ``entry_points`` to manage all its pluggable resources.
Let's create a small python package
to accomodate our handler. Lets create a new directory ``solar_pg``
with a setup.py file

.. code-block:: python

    from setuptools import setup

    setup(
        name='solar-pg',
        version='1.0.0',
        py_modules='solar_pg',
        entry_points={
            'solar.handlers': [
                'psql=solar_pg:PgHandler'
            ]
        }
    )

Now let's implement our handler.
As it will be based on action files we will use
:py:class:`solar.core.handlers.base.TempFileHandler`
We want our handler to process our SQL files
so we can use our inputs.
Then to upload these files to a node,
and lastly to execute the SQL files.

.. code-block:: python

    from psycopg2.extensions import adapt


    from solar import errors
    from solar.core.handlers.base import TempFileHandler
    from solar.core.log import log


    class PgHandler(TempFileHandler):

        def action(self, resource, action_name):
            action_file = self._compile_action_file(resource, action_name)
            action_file_name = '/tmp/{}.sql'.format(resource.name)
            self.prepare_templates_and_scripts(resource, action_file, '')
            self.transport_sync.copy(
                resource, action_file, action_file_name, use_sudo=True
            )
            self.transport_sync.sync_all()

            self.transport_run.run(
                resource,
                'chown', 'postgres:postgres', action_file_name,
                use_sudo=True
            )
            cmd_args = [
                'su', 'postgres', '-c',
                'postgres psql -f {}'.format(action_file_name),
            ]
            res = self.transport_run.run(
                resource,
                *cmd_args,
                use_sudo=True,
                warn_only=True
            )
            rc, out, err = res.return_code, res.stdout, res.stderr
            log.debug('CMD %r RC %s OUT %s ERR %s', cmd_args, rc, out, err)
            if rc != 0:
                raise errors.SolarError('psql for {} failed with RC {}'.format(
                    resource.name, rc
                ))

        def _render_action(self, resource, action):
            action_file = resource.actions[action]
            args = self._make_args(resource)
            result = [
                '\\set {} {}'.format(key, adapt(value).getquoted())
                for key, value in args.items()
                if type(value) in {str, unicode, int}
            ]
            with open(action_file) as f:
                result.append(f.read())
            return '\n'.join(result)

We define two methods here.
First is ``.action()`` which is a main entry point of our handler.
This method calls *transports* to perform actual heavy lifting.
We use transport_sync to copy the action file
(we need sudo, as the file from previous run can be there
with user set to postgres).
The transport_sync schedules jobs and executes them on ``sync_all()``.
If we put some templates or scripts in our resource,
then ``prepare_templates_and_scripts`` will schedule their transfer as well.
We use transport_run to execute commands on the remote side.

We have also overridden ``_render_action`` method.
The default one performs jinja substitutions
and it is good for languages that don't have any variables
(like YAML).
For languages that have variables
it might be smarter to use them instead of jinja.
So we use the Postgresql ``\set`` directives to set the values.

That's all - we created a functional solar handler that handles SQL.


4. Resources for our handler
-------------------------------

Now we can create some resources for our handler
First a resource for a Postgres role. In file
``postgres_repo/role/1.0.0/meta.yaml``:

.. code-block:: yaml

    handler: psql
    actions:
        run: run.sql
        remove: remove.sql
    input:
        username:
            schema: str!
            value:
        password:
            schema: str!
            value:

And then in file ``postgres_repo/role/1.0.0/actions/run.sql``:

.. code-block:: sql

    CREATE ROLE :username WITH PASSWORD :password LOGIN;

Finally in file ``postgres_repo/role/1.0.0/actions/remove.sql``:

.. code-block:: sql

    DROP ROLE :username;

It is now trivial to create a "database" resource.
Use the "role" resource as a base,
add two inputs: ``name`` and ``owner``
and then modify the SQL files accordingly.


.. code-block:: sql

    -- run.sql
    CREATE DATABASE :name WITH OWNER :owner;
    -- remove.sql
    DROP DATABASE :name;


5. Another handler based on Fabric tool
-----------------------------------------

Fabric is a python tool for task execution.
Although it offers us its own mechanism to handle remote servers via ssh,
we shouldn't be tempted to use it.
The solar idea of 'transport' is much more powerful
than simple ssh remote execution.
That's why we would let Solar's transports
to copy the fabfile and execute it on the target node.

Let's create a package similar to the ``solar_pg`` above.

.. code-block:: python

    # setup.py

    from setuptools import setup

    setup(
        name='solar_fab',
        version='1.0.0',
        py_modules='solar_fab',
        entry_points={
            'solar.handlers':
                [
                    'fab=solar_fab:FabHandler'
                ]
        }
    )

    # solar_fab.py

    import os

    from solar import errors
    from solar.core.handlers.base import TempFileHandler
    from solar.core.log import log

    class FabHandler(TempFileHandler):

        def _make_args(self, resource):
            args = {
                'resource_name': resource.name,
                'resource_dir': self.dirs[resource.name],
            }
            args.update(resource.args)
            return args

        def action(self, resource, action_name):
            action_file = os.path.join(resource.base_path, 'fabfile.py')
            action_file_name = '/tmp/{}.py'.format(resource.name)
            self.prepare_templates_and_scripts(resource, action_file, '')
            self.transport_sync.copy(resource, action_file, action_file_name)
            self.transport_sync.sync_all()
            arg_string = ':' + ','.join(
                '{}={}'.format(k, v)
                    for k, v in self._make_args(resource).iteritems()
            )
            cmd_args = ['fab', '-f', action_file_name, action_name+arg_string]
            res = self.transport_run.run(
                resource,
                *cmd_args,
                use_sudo=False,
                warn_only=True
            )
            rc, out, err = res.return_code, res.stdout, res.stderr
            log.debug('CMD %r RC %s OUT %s ERR %s', cmd_args, rc, out, err)
            if rc != 0:
                raise errors.SolarError(
                    'Fab for {} failed with RC {}'.format(
                        resource.name, rc)
                )


Due to the fact,
that fabric allows us to put actions in a single file
we change the action_file logic a little.
The general idea is similar to the previous handler.
Instead of sending the args by editing the fabfile,
we send them fabric way with command line arguments.

6. Installing shootout with our handler
---------------------------------------

Shootout is a simple discussion application
created to illustrate basic configuration
of a Pyramid app with SQLAlchemy.

To install it we will use two fab-based resources.
One will create the virtualenv for our app.
It would be fully reusable.
The other will be specific to our app

.. code-block:: yaml

    # app_repo/virtualenv/1.0.0/meta.yaml

    handler: fab
    version: 1.0.0
    actions:
        run: run
        remove: remove
    input:
        path:
            schema: str!
            value:
        python:
            schema: str!
            value:

.. code-block:: python

    # app_repo/virtualenv/1.0.0/fabfile.py

    from fabric.api import local

    def run(path, python, **kwargs):
        local('virtualenv --python={} {}'.format(python, path))


    def remove(path, **kwargs)
        local('rm -rf {}'.format(python, path))

The above is self-explanatory.
For our application resource however
we need to provide a configuration file
that will be separate from the fabfile,
but will be processed by jinja.
Execute:

.. code-block:: bash

    $ wget -Papp_repo/shootout/1.0.0/templates/ https://raw.githubusercontent.com/Pylons/shootout/master/development.ini

Then edit the file you downloaded,
so the lines for session secret and sql URL are:

.. code-block:: ini

    session.secret = {{ secret }}
    sqlalchemy.url = postgresql:{{ db_username }}:{{ db_password[1:-1] }}//127.0.0.1/{{ db_name }}

Lastly create the meta file and the fabfile:

.. code-block:: yaml

    # app_repo/shootout/1.0.0/meta.yaml

    handler: fab
    version: 1.0.0
    actions:
        run: run
        remove: remove
    input:
        secret:
            schema: str!
            value:
        db_name:
            schema: str!
            value:
        db_username:
            schema: str!
            value:
        db_password:
            schema: str!
            value:
        virtualenv:
            schema: str!
            value:


.. code-block:: python

    from fabric.api import local


    def venv_run(virtualenv, cmd):
        local('. {}/bin/activate && {}'.format(virtualenv, cmd))


    def run(virtualenv, resource_dir, **kwargs):
        venv_run(
            virtualenv,
            'pip install git+https://github.com/Pylons/shootout.git'
        )
        local('cp {}/templates/development.ini .'.format(resource_dir))
        venv_run(
            virtualenv,
            'pip install psycopg2'
        )
        venv_run(
            virtualenv,
            'initialize_shootout_db development.ini'
        )
        venv_run(
            virtualenv,
            'pserve --daemon development.ini'
        )

    def remove(virtualenv, **kwargs):
        venv_run(
            virtualenv,
            'pip uninstall shootout'
        )

As you can see we use a variable called ``resource_dir``
that our handler passed to fabric.
This directory will be a temporary one.
It is our task to make sense of the templates,
move them to appropriate locations and use.


7. Putting it all together
--------------------------

Now we can put it all together
with composer file as before.
In file: ``app_repo/app/1.0.0/app.yaml``
let's put:

.. code-block:: yaml

    resources:
        -
            id: postgresql
            from: postgres/postgresql
            input: {}

        -
            id: pg_role
            from: postgres/role
            input:
                username: user1
                password: us3rp4ss
        -
            id: pg_db
            from: postgres/db
            input:
                name: my_db
                owner: pg_role::username
        -
            id: virtualenv
            from: app/virtualenv
            input:
                name: app_venv
                python: /usr/bin/python2.7
        -
            id: shootout
            from: app/shootout
            input:
                secret: shhhhh
                db_name: pg_db::name
                db_username: pg_role::username
                db_password: pg_role::password
                virtualenv: virtualenv::name
    events:
        -
            type: depends_on
            parent_action: postgresql.run
            child_action: pg_role.run
        -
            type: depends_on
            parent_action: pg_role.remove
            child_action: postgresql.removee

A new thing here is the ``events`` section.
The reason for it is that
while we don't use any variables from
``postgresql`` resource in ``pg_role`` resource,
we still want the former to be run before the latter.

Now as before call:

.. code-block:: bash

    $ solar repo import -n postgres postgres_repo/
    $ solar repo import -n app app_repo/
    $ solar resource create nodes templates/nodes count=1
    $ solar resource create shootout app/app
    $ solar changes stage
    $ solar changes process
    $ solar orch run-once

After solar finishes the installation,
visit http://10.0.0.3:6543 to see the working application.
