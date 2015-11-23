from riak import RiakClient as OrigRiakClient
import time

from solar.dblayer.model import clear_cache


class RiakClient(OrigRiakClient):

    def session_start(self):
        clear_cache()

    def session_end(self, result=True):
        # ignore result
        clear_cache()

    def delete_all(self, cls):
        for _ in xrange(10):
            # riak dislikes deletes without dvv
            rst = cls.bucket.get_index('$bucket', startkey='_', max_results=100000).results
            for key in rst:
                cls.bucket.delete(key)
            else:
                return
            time.sleep(0.5)

