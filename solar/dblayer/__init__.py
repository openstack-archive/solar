try:
    from gevent import monkey
except ImportError:
    pass
else:
    from solar.dblayer.gevent_patches import patch_all
    patch_all()

from solar.dblayer.model import ModelMeta
from solar.config import C
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
else:
    raise Exception('Unknown dblayer backend %s', C.solar_db)

ModelMeta.setup(client)

from solar.dblayer import standalone_session_wrapper
standalone_session_wrapper.create_all()
