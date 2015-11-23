import wrapt


class DBLayerProxy(wrapt.ObjectProxy):

    def __init__(self, wrapped):
        super(DBLayerProxy, self).__init__(wrapped)
        refs = wrapped._c.refs
        refs[wrapped.key].add(self)

    def next(self, *args, **kwargs):
        return self.__wrapped__.next(*args, **kwargs)
