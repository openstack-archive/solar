from threading import local, current_thread
from random import getrandbits
import uuid
from functools import wraps
from operator import itemgetter


LOCAL = local()

class DBLayerException(Exception):
    pass


class DBLayerNotFound(DBLayerException):
    pass


class DBLayerNoRiakObj(DBLayerException):
    pass


class NONE:
    """A None like type"""
    pass

def get_cache(instance, _):
    th = current_thread()
    l = LOCAL
    try:
        cache_id = l.cache_id
    except AttributeError:
        cache_id = uuid.UUID(int=getrandbits(128), version=4).hex
        setattr(th, 'cache_id', cache_id)
    if getattr(th, 'cache_id', None) == cache_id:
        setattr(l, 'obj_cache', {})
        setattr(l, 'db_ch_state', {})
        l.db_ch_state.setdefault('index', set())
    return l


def clear_cache():
    th = current_thread()
    cache_id = uuid.UUID(int=getrandbits(128), version=4).hex
    setattr(th, 'cache_id', cache_id)


def get_bucket(_, owner, mcs):
    name = owner.get_bucket_name()
    bucket = mcs.riak_client.bucket(name)
    return bucket


def changes_state_for(_type):
    def _inner1(f):
        @wraps(f)
        def _inner2(obj, *args, **kwargs):
            obj._c.db_ch_state['index'].add(obj.key)
            return f(obj, *args, **kwargs)
        return _inner2
    return _inner1


def clears_state_for(_type):
    def _inner1(f):
        @wraps(f)
        def _inner2(obj, *args, **kwargs):
            try:
                obj._c.db_ch_state[_type].remove(obj.key)
            except KeyError:
                pass
            return f(obj, *args, **kwargs)
        return _inner2
    return _inner1


def requires_clean_state(_type):
    def _inner1(f):
        @wraps(f)
        def _inner2(obj, *args, **kwargs):
            check_state_for(_type, obj)
            return f(obj, *args, **kwargs)
        return _inner2
    return _inner1


def check_state_for(_type, obj):
    state = obj._c.db_ch_state.get(_type)
    if state:
        raise Exception("Dirty state, save all objects first")


class Replacer(object):

    def __init__(self, name, fget, *args):
        self.name = name
        self.fget = fget
        self.args = args

    def __get__(self, instance, owner):
        val = self.fget(instance, owner, *self.args)
        if instance is not None:
            setattr(instance, self.name, val)
        else:
            setattr(owner, self.name, val)
        return val


class FieldBase(object):
    def __init__(self, fname, default):
        self._fname = fname
        self._default = default

    @property
    def fname(self):
        return self._fname

    @fname.setter
    def fname(self, value):
        if self._fname is None:
            self._fname = value
        else:
            raise Exception("fname already set")

    @property
    def default(self):
        if self._default is NONE:
            return self._default
        if callable(self._default):
            return self._default()
        return self._default


class Field(FieldBase):

    def __init__(self, _type, fname=None, default=NONE):
        self._type = _type
        super(Field, self).__init__(fname=fname, default=default)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance._riak_object.data[self.fname]

    def __set__(self, instance, value):
        if not isinstance(value, self._type):
            raise Exception("Invalid type %r for %r" % (type(value), self.fname))
        instance._modified_fields.add(self.fname)
        instance._riak_object.data[self.fname] = value

    def __str__(self):
        return "<%s:%r>" % (self.__class__.__name__, self.fname)

    __repr__ = __str__


class IndexFieldWrp(object):

    def __init__(self, field_obj, instance):
        self._field_obj = field_obj
        self._instance = instance
        self._c = self._instance._c

    @property
    def fname(self):
        return self._field_obj.fname

    def __str__(self):
        return "<%s for field %s>" % (self.__class__.__name__, self._field_obj)

    def _get_field_val(self, name):
        return self._instance._riak_object.data[self.fname][name]

    def __getitem__(self, name):
        return self._get_field_val(name)

    def __setitem__(self, name, value):
        inst = self._instance
        inst._riak_object.set_index('%s_bin' % self.fname, '{}|{}'.format(name, value))

    def __delitem__(self, name):
        inst = self._instance
        del inst._riak_object.data[self.fname][name]
        indexes = inst._riak_object.indexes

        # TODO: move this to backend layer
        for ind_name, ind_value in indexes:
            if ind_name == ('%s_bin' % self.fname):
                if ind_value.startswith('{}|'.format(name)):
                    inst._remove_index(ind_name, ind_value)
                    break


class IndexField(FieldBase):

    _wrp_class = IndexFieldWrp

    def __init__(self, fname=None, default=NONE):
        super(IndexField, self).__init__(fname, default)

    def _on_no_inst(self, instance, owner):
        return self

    def __get__(self, instance, owner):
        if instance is None:
            return self._on_no_inst(instance, owner)
        cached = getattr(instance, '_real_obj_%s' % self.fname, None)
        if cached:
            return cached
        obj = self._wrp_class(self, instance)
        setattr(instance, '_real_obj_%s' % self.fname, obj)
        return obj

    def __set__(self, instance, value):
        wrp = getattr(instance, self.fname)
        instance._riak_object.data[self.fname] = self.default
        for f_name, f_value in value.iteritems():
            wrp[f_name] = f_value


    def _parse_key(self, k):
        if '=' in k:
            val, subval = k.split('=', 1)
        if subval is None:
            subval = ''
        if not isinstance(subval, basestring):
            subval = str(subval)
        return '{}|{}'.format(val, subval)

    def filter(self, startkey, endkey=None, **kwargs):
        startkey = self._parse_key(startkey)
        if endkey is None:
            if startkey.endswith('*'):
                startkey = startkey[:-1]
                endkey = startkey + '~'
            else:
                endkey = startkey + ' '
        kwargs.setdefault('max_results', 1000000)
        kwargs['return_terms'] = False
        res = self._declared_in._get_index('{}_bin'.format(self.fname),
                                           startkey=startkey,
                                           endkey=endkey,
                                           **kwargs).results
        return set(res)




class ModelMeta(type):

    def __new__(mcs, name, bases, attrs):
        cls = super(ModelMeta, mcs).__new__(mcs, name, bases, attrs)
        model_fields = set((name for (name, attr) in attrs.items()
                            if isinstance(attr, FieldBase) and not name.startswith('_')))
        for f in model_fields:
            field = getattr(cls, f)
            if hasattr(field, 'fname') and field.fname is None:
                setattr(field, 'fname', f)
            setattr(field, 'gname', f)
            # need to set declared_in because `with_tag`
            # no need to wrap descriptor with another object then
            setattr(field, '_declared_in', cls)

        for base in bases:
            try:
                model_fields_base  = base._model_fields
            except AttributeError:
                continue
            else:
                for given in base._model_fields:
                    model_fields.add(given)

        # set the fields just in case
        cls._model_fields = [getattr(cls, x) for x in model_fields]

        cls.bucket = Replacer('bucket', get_bucket, mcs)
        return cls


    @classmethod
    def setup(mcs, riak_client):
        mcs.riak_client = riak_client


class Model(object):

    __metaclass__ = ModelMeta

    _c = Replacer('_c', get_cache)

    _key = None
    _new = None
    _real_riak_object = None

    _changed = False

    def __init__(self, key=None):
        self._modified_fields = set()
        self.key = key

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, value):
        if self._key is None:
            self._key = value
        else:
            raise Exception("Can't set key again")

    @property
    def _riak_object(self):
        if self._real_riak_object is None:
            raise DBLayerNoRiakObj("You cannot access _riak_object now")
        return self._real_riak_object

    @_riak_object.setter
    def _riak_object(self, value):
        if self._real_riak_object is not None:
            raise DBLayerException("Already have _riak_object")
        self._real_riak_object = value

    @changes_state_for('index')
    def _set_index(self, *args, **kwargs):
        return self._riak_object.set_index(*args, **kwargs)

    @changes_state_for('index')
    def _add_index(self, *args, **kwargs):
        return self._riak_object.add_index(*args, **kwargs)

    @changes_state_for('index')
    def _add_index(self, *args, **kwargs):
        return self._riak_object.add_index(*args, **kwargs)

    @changes_state_for('index')
    def _remove_index(self, *args, **kwargs):
        return self._riak_object.remove_index(*args, **kwargs)

    @classmethod
    def _get_index(cls, *args, **kwargs):
        return cls.bucket.get_index(*args, **kwargs)

    @property
    def _bucket(self):
        return self._riak_object.bucket

    @classmethod
    def get_bucket_name(cls):
        # XXX: should be changed and more smart
        return cls.__name__

    def changed(self):
        return True if self._modified_fields else False

    def __str__(self):
        if self._riak_object is None:
            return "<%s not initialized>" % (self.__class__.__name__)
        return "<%s %s:%s>" % (self.__class__.__name__, self._riak_object.bucket.name, self.key)


    @classmethod
    def new(cls, key, data):
        return cls.from_dict(key, data)

    @classmethod
    def from_riakobj(cls, riak_obj):
        obj = cls(riak_obj.key)
        obj._riak_object = riak_obj
        if obj._new is None:
            obj._new = False
        cls._c.obj_cache[riak_obj.key] = obj
        return obj

    @classmethod
    def from_dict(cls, key, data=None):
        if isinstance(key, dict) and data is None:
            data = key
            try:
                key = data['key']
            except KeyError:
                raise DBLayerException("No key specified")
        if key and 'key' in data and data['key'] != key:
            raise DBLayerException("Different key values detected")
        data['key'] = key
        riak_obj = cls.bucket.new(key, data={})
        obj = cls.from_riakobj(riak_obj)
        obj._new = True
        for field in cls._model_fields:
            # if field is cls._pkey_field:
            #     continue  # pkey already set
            fname = field.fname
            gname = field.gname
            val = data.get(fname, NONE)
            default = field.default
            if val is NONE and default is not NONE:
                setattr(obj, gname, default)
            elif val is not NONE:
                setattr(obj, gname, val)
        return obj

    @classmethod
    def get(cls, key):
        try:
            return cls._c.obj_cache[key]
        except KeyError:
            riak_object = cls.bucket.get(key)
            if not riak_object.exists:
                raise DBLayerNotFound(key)
            else:
                obj = cls.from_riakobj(riak_object)
                return obj

    @clears_state_for('index')
    def save(self, force=False):
        if self.changed() or force or self._new:
            return self._riak_object.store()
        else:
            raise Exception("No changes")
