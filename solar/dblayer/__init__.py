# -*- coding: utf-8 -*-
#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


try:
    from gevent import monkey  # NOQA
except ImportError:
    pass
else:
    from solar.dblayer.gevent_patches import patch_all
    patch_all()

from solar.config import C
from solar.dblayer.model import ModelMeta
from solar.utils import parse_database_conn

_connection, _connection_details = parse_database_conn(C.solar_db)

if _connection.mode == 'sqlite':
    from solar.dblayer.sql_client import SqlClient
    if _connection.database == ':memory:' or _connection.database is None:
        opts = {'threadlocals': True,
                'autocommit': False}
        _connection.database = ":memory:"
    else:
        opts = {'threadlocals': True,
                'autocommit': False,
                'pragmas': (('journal_mode', 'WAL'),
                            ('synchronous', 'NORMAL'))}
    opts.update(_connection_details.toDict())
    opts.setdefault('db_class', 'SqliteDatabase')
    client = SqlClient(
        _connection.database,
        **opts)

elif _connection.mode == 'riak':
    from solar.dblayer.riak_client import RiakClient
    proto = _connection_details.get('protocol', 'pbc')
    opts = _connection_details.toDict()
    if proto == 'pbc':
        client = RiakClient(protocol=proto,
                            host=_connection.host,
                            pb_port=_connection.port,
                            **opts)
    elif proto == 'http':
        client = RiakClient(protocol=proto,
                            host=C.solar_db.host,
                            http_port=_connection.port,
                            **opts)
    else:
        raise Exception('Unknown riak protocol %s', proto)

elif _connection.mode == 'postgresql':
    # TODO: collation has to be `C`
    from solar.dblayer.sql_client import SqlClient
    opts = {'autocommit': False}
    opts.update(_connection_details.toDict())
    if _connection.port:
        _connection.port = int(_connection.port)
    else:
        _connection.port = None
    opts["user"] = _connection.username
    opts["host"] = _connection.host
    opts["port"] = _connection.port
    opts["password"] = _connection.password
    # TODO: allow set Postgresql classes from playhouse
    opts.setdefault('db_class', 'PostgresqlDatabase')
    client = SqlClient(_connection.database,
                       **opts)
else:
    raise Exception('Unknown dblayer backend %s', C.solar_db)

ModelMeta.setup(client)

from solar.dblayer import standalone_session_wrapper
standalone_session_wrapper.create_all()
