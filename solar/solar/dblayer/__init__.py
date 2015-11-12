from solar.dblayer.model import ModelMeta
from solar.dblayer.riak_client import RiakClient

client = RiakClient(protocol='pbc', host='10.0.0.2', pb_port=8087)
# client = RiakClient(protocol='http', host='10.0.0.2', http_port=8098)

ModelMeta.setup(client)

from solar.dblayer import standalone_session_wrapper
standalone_session_wrapper.create_all()
