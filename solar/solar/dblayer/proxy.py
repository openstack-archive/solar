import wrapt


class DBLayerProxy(wrapt.ObjectProxy):

    def __init__(self, wrapped):
        super(DBLayerProxy, self).__init__(wrapped)
        refs = wrapped._c.refs
        refs[wrapped.key].add(self)
