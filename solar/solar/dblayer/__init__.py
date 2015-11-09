from solar.dblayer.model import ModelMeta
from solar.dblayer.riak_client import RiakClient
from solar.config import C

client = RiakClient(
    protocol=C.riak.protcol, host=C.riak.host, pb_port=C.riak.port)
# client = RiakClient(protocol='http', host='10.0.0.2', http_port=8098)

ModelMeta.setup(client)
