from gevent.pool import Pool
import gevent


class DBLayerPool(Pool):

    def __init__(self, *args, **kwargs):
        super(DBLayerPool, self).__init__(*args, **kwargs)
        self.parent = gevent.getcurrent()

    def spawn(self, *args, **kwargs):
        greenlet = self.greenlet_class(*args, **kwargs)
        greenlet._nested_parent = self.parent
        self.start(greenlet)
        return greenlet
