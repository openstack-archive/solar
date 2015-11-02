from gevent.pool import Pool
import gevent
from solar.dblayer.solar_models import Resource


class DBLayerPool(Pool):

    def __init__(self, *args, **kwargs):
        super(DBLayerPool, self).__init__(*args, **kwargs)
        self.parent = gevent.getcurrent()

    def spawn(self, *args, **kwargs):
        greenlet = self.greenlet_class(*args, **kwargs)
        greenlet._nested_parent = self.parent
        self.start(greenlet)
        return greenlet


@classmethod
def multi_get(obj, keys):
    pool = DBLayerPool(5)
    return pool.map(obj.get, keys)


def solar_map(funct, args, concurrency=5):
    dp = DBLayerPool(concurrency)
    return dp.map(funct, args)


def get_local():
    from solar.dblayer.gevent_local import local
    return local
