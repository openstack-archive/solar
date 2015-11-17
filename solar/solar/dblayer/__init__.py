from solar.dblayer.model import ModelMeta
from solar.dblayer.riak_client import RiakClient
from solar.config import C

if C.dblayer == 'sqlite':
    from solar.dblayer.sql_client import SqlClient
    if C.sqlite.backend == 'memory':
        client = SqlClient(C.sqlite.location, threadlocals=False, autocommit=False)
    elif C.sqlite.backend == 'file':
        client = SqlClient(C.sqlite.location, threadlocals=True,
            autocommit=False, pragmas=(('journal_mode', 'WAL'),
                                       ('synchronous', 'NORMAL')))
    else:
        raise Exception('Unknown sqlite backend %s', C.sqlite.backend)

elif C.dblayer == 'riak':
    from solar.dblayer.riak_client import RiakClient
    if C.riak.protocol == 'pbc':
       client = RiakClient(
            protocol=C.riak.protocol, host=C.riak.host, pb_port=C.riak.port)
    elif C.riak.protocol == 'http':
        client = RiakClient(
            protocol=C.riak.protocol, host=C.riak.host, http_port=C.riak.port)
    else:
        raise Exception('Unknown riak protocol %s', C.riak.protocol)
else:
    raise Exception('Unknown dblayer backend %s', C.dblayer)

ModelMeta.setup(client)

from solar.dblayer import standalone_session_wrapper
standalone_session_wrapper.create_all()
