from solar.dblayer.model import ModelMeta
from solar.dblayer.riak_client import RiakClient
from solar.config import C


if C.solar_db.mode == 'sqlite':
    from solar.dblayer.sql_client import SqlClient
    if C.solar_db.backend == 'memory':
        client = SqlClient(C.solar_db.location, threadlocals=False, autocommit=False)
    elif C.solar_db.backend == 'file':
        client = SqlClient(C.solar_db.location, threadlocals=True,
            autocommit=False, pragmas=(('journal_mode', 'WAL'),
                                       ('synchronous', 'NORMAL')))
    else:
        raise Exception('Unknown sqlite backend %s', C.solar_db.backend)

elif C.solar_db.mode == 'riak':
    from solar.dblayer.riak_client import RiakClient
    if C.solar_db.protocol == 'pbc':
       client = RiakClient(
            protocol=C.solar_db.protocol, host=C.solar_db.host, pb_port=C.solar_db.port)
    elif C.solar_db.protocol == 'http':
        client = RiakClient(
            protocol=C.solar_db.protocol, host=C.solar_db.host, http_port=C.solar_db.port)
    else:
        raise Exception('Unknown riak protocol %s', C.solar_db.protocol)
else:
    raise Exception('Unknown dblayer backend %s', C.dblayer)

ModelMeta.setup(client)

from solar.dblayer import standalone_session_wrapper
standalone_session_wrapper.create_all()
