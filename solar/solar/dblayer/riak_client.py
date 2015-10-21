from riak import RiakClient as OrigRiakClient

from solar.dblayer.model import clear_cache


class RiakClient(OrigRiakClient):

    def session_start(self):
        clear_cache()

    def session_end(self, result=True):
        # ignore result
        clear_cache()
