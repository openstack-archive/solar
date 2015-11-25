"""
This code is slight modification of gevent.local

Original file is MIT licensed.

For details please refer for gevent license
"""

from copy import copy
from weakref import ref
from contextlib import contextmanager
from gevent.hub import getcurrent, PYPY
from gevent.lock import RLock

__all__ = ["local"]


class _wrefdict(dict):
    """A dict that can be weak referenced"""


class _localimpl(object):
    """A class managing thread-local dicts"""
    __slots__ = 'key', 'dicts', 'localargs', 'locallock', '__weakref__'

    def __init__(self):
        # The key used in the Thread objects' attribute dicts.
        # We keep it a string for speed but make it unlikely to clash with
        # a "real" attribute.
        self.key = '_threading_local._localimpl.' + str(id(self))
        # { id(Thread) -> (ref(Thread), thread-local dict) }
        self.dicts = _wrefdict()

    def find_parent(self):
        """
        Iterate to top most parent, and use it as a base
        """
        c = getcurrent()
        while 1:
            tmp_c = getattr(c, '_nested_parent', c.parent)
            if not tmp_c:
                return c
            c = tmp_c

    def get_dict(self):
        """Return the dict for the current thread. Raises KeyError if none
        defined."""
        # thread = getcurrent()
        thread = self.find_parent()
        return self.dicts[id(thread)][1]

    def create_dict(self):
        """Create a new dict for the current thread, and return it."""
        localdict = {}
        key = self.key
        thread = self.find_parent()
        idt = id(thread)

        # If we are working with a gevent.greenlet.Greenlet, we can
        # pro-actively clear out with a link. Use rawlink to avoid
        # spawning any more greenlets
        try:
            rawlink = thread.rawlink
        except AttributeError:
            # Otherwise we need to do it with weak refs
            def local_deleted(_, key=key):
                # When the localimpl is deleted, remove the thread attribute.
                thread = wrthread()
                if thread is not None:
                    del thread.__dict__[key]

            def thread_deleted(_, idt=idt):
                # When the thread is deleted, remove the local dict.
                # Note that this is suboptimal if the thread object gets
                # caught in a reference loop. We would like to be called
                # as soon as the OS-level thread ends instead.
                _local = wrlocal()
                if _local is not None:
                    _local.dicts.pop(idt, None)

            wrlocal = ref(self, local_deleted)
            wrthread = ref(thread, thread_deleted)
            thread.__dict__[key] = wrlocal
        else:
            wrdicts = ref(self.dicts)

            def clear(_):
                dicts = wrdicts()
                if dicts:
                    dicts.pop(idt, None)

            rawlink(clear)
            wrthread = None

        self.dicts[idt] = wrthread, localdict
        return localdict


@contextmanager
def _patch(self):
    impl = object.__getattribute__(self, '_local__impl')
    orig_dct = object.__getattribute__(self, '__dict__')
    try:
        dct = impl.get_dict()
    except KeyError:
        # it's OK to acquire the lock here and not earlier,
        # because the above code won't switch out
        # however, subclassed __init__ might switch,
        # so we do need to acquire the lock here
        dct = impl.create_dict()
        args, kw = impl.localargs
        with impl.locallock:
            self.__init__(*args, **kw)
    with impl.locallock:
        object.__setattr__(self, '__dict__', dct)
        yield
        object.__setattr__(self, '__dict__', orig_dct)


class local(object):
    __slots__ = '_local__impl', '__dict__'

    def __new__(cls, *args, **kw):
        if args or kw:
            if (PYPY and cls.__init__ == object.__init__) or (
                    not PYPY and cls.__init__ is object.__init__):
                raise TypeError("Initialization arguments are not supported")
        self = object.__new__(cls)
        impl = _localimpl()
        impl.localargs = (args, kw)
        impl.locallock = RLock()
        object.__setattr__(self, '_local__impl', impl)
        # We need to create the thread dict in anticipation of
        # __init__ being called, to make sure we don't call it
        # again ourselves.
        impl.create_dict()
        return self

    def __getattribute__(self, name):
        with _patch(self):
            return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name == '__dict__':
            raise AttributeError("%r object attribute '__dict__' is read-only"
                                 % self.__class__.__name__)
        with _patch(self):
            return object.__setattr__(self, name, value)

    def __delattr__(self, name):
        if name == '__dict__':
            raise AttributeError("%r object attribute '__dict__' is read-only"
                                 % self.__class__.__name__)
        with _patch(self):
            return object.__delattr__(self, name)

    def __copy__(self):
        impl = object.__getattribute__(self, '_local__impl')
        current = impl.find_parent()
        currentId = id(current)
        d = impl.get_dict()
        duplicate = copy(d)

        cls = type(self)
        if (PYPY and cls.__init__ != object.__init__) or (
                not PYPY and cls.__init__ is not object.__init__):
            args, kw = impl.localargs
            instance = cls(*args, **kw)
        else:
            instance = cls()

        new_impl = object.__getattribute__(instance, '_local__impl')
        tpl = new_impl.dicts[currentId]
        new_impl.dicts[currentId] = (tpl[0], duplicate)

        return instance
