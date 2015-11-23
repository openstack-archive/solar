import wrapt


class DBLayerProxy(wrapt.ObjectProxy):

    def __init__(self, wrapped):
        super(DBLayerProxy, self).__init__(wrapped)
        refs = wrapped._c.refs
        refs[wrapped.key].add(self)

    def next(self, *args, **kwargs):
        return self.__wrapped__.next(*args, **kwargs)

    def __hash__(self):
        # id is there by intention
        # we override __has__ in model
        return hash(id(self.__wrapped__))

    def __eq__(self, other):
        if not isinstance(other, DBLayerProxy):
            return self.__wrapped__ == other
        return self.__wrapped__ == self.__wrapped__

    def __repr__(self):
        return "<P: %r>" % self.__wrapped__
