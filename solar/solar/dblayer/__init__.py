from solar.dblayer.model import ModelMeta
from solar.dblayer.riak_client import RiakClient
client = RiakClient(protocol='pbc', host='10.0.0.3', pb_port=18087)
# client = RiakClient(protocol='http', host='10.0.0.3', http_port=18098)

ModelMeta.setup(client)
