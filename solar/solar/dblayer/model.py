from threading import local, current_thread
from random import getrandbits
import uuid
from functools import wraps, total_ordering
from operator import itemgetter
import time

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


class SingleClassCache(object):

    __slots__ = ['obj_cache', 'db_ch_state', 'lazy_save', 'origin_class']

    def __init__(self, origin_class):
        self.obj_cache = {}
        self.db_ch_state = {'index': set()}
        self.lazy_save = set()
        self.origin_class = origin_class


class ClassCache(object):

    def __get__(self, _, owner):
        th = current_thread()
        l = LOCAL
        # better don't duplicate class names
        cache_name = owner.__name__
        try:
            cache_id = l.cache_id
        except AttributeError:
            cache_id = uuid.UUID(int=getrandbits(128), version=4).hex
            setattr(l, 'cache_id', cache_id)
        if getattr(th, 'cache_id', None) != cache_id:
            # new cache
            setattr(th, 'cache_id', cache_id)
            c = SingleClassCache(owner)
            setattr(l, '_model_caches', {})
            l._model_caches[cache_name] = c
        try:
            # already had this owner in cache
            return l._model_caches[cache_name]
        except KeyError:
            # old cache but first time this owner
            c = SingleClassCache(owner)
            l._model_caches[cache_name] = c
            return c


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


@total_ordering
class StrInt(object):

    precision = 3
    positive_char = 'p'
    negative_char = 'n'
    format_size = 10 + precision


    def __init__(self, val=None):
        self._val = self._make_val(val)

    def __str__(self):
        return self._val.__str__()

    def __repr__(self):
        return "<%s: %r>" % (self.__class__.__name__, self._val)

    @classmethod
    def p_max(cls):
        return cls(int('9' * cls.format_size))

    @classmethod
    def p_min(cls):
        return cls(1)

    @classmethod
    def n_max(cls):
        return -cls.p_max()

    @classmethod
    def n_min(cls):
        return -cls.p_min()

    def __neg__(self):
        time_ = self.int_val()
        ret = self.__class__(-time_)
        return ret

    @classmethod
    def to_hex(cls, value):
        char = cls.positive_char
        if value < 0:
            value = int('9' * cls.format_size) + value
            char = cls.negative_char
        f = '%s%%.%dx' % (char, cls.format_size - 2)
        value = f % value
        if value[-1] == 'L':
            value = value[:-1]
        return value

    @classmethod
    def from_hex(cls, value):
        v = int(value[1:], 16)
        if value[0] == cls.negative_char:
            v -= int('9' * self.format_size)
        return v

    def int_val(self):
        return self.from_hex(self._val)

    @classmethod
    def from_simple(cls, value):
        return cls(value)

    @classmethod
    def to_simple(cls, value):
        return value._val

    @classmethod
    def _make_val(cls, val):
        if val is None:
            val = time.time()
        if isinstance(val, (long, int, float)):
            if isinstance(val, float):
                val = int(val * (10 ** cls.precision))
            val = cls.to_hex(val)
        elif isinstance(val, cls):
            val = val._val
        return val

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            raise Exception("Cannot compare %r with %r" % (self, other))
        so = other._val[0]
        ss = self._val[0]
        son = so == other.negative_char
        ssn = so == self.negative_char
        if son != ssn:
            return False
        return self._val[1:] == other._val[1:]

    def __gt__(self, other):
        if not isinstance(other, self.__class__):
            raise Exception("Cannot compare %r with %r" % (self, other))
        so = other._val[0]
        ss = self._val[0]
        if ss == self.positive_char and so == other.negative_char:
            return -1
        elif ss == self.negative_char and so == other.positive_char:
            return 1
        else:
            return other._val[1:] < self._val[1:]



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

    _simple_types = {int, float, long, str, unicode, basestring, list, tuple, dict}

    def __init__(self, _type, fname=None, default=NONE):
        self._type = _type
        super(Field, self).__init__(fname=fname, default=default)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        val = instance._data_container[self.fname]
        if self._type in self._simple_types:
            return val
        else:
            return self._type.from_simple(val)

    def __set__(self, instance, value):
        if not isinstance(value, self._type):
            raise Exception("Invalid type %r for %r" % (type(value), self.fname))
        if self._type not in self._simple_types:
            value = self._type.to_simple(value)
        instance._field_changed(self)
        instance._data_container[self.fname] = value
        return value

    def __str__(self):
        return "<%s:%r>" % (self.__class__.__name__, self.fname)

    __repr__ = __str__


class IndexedField(Field):

    def __set__(self, instance, value):
        value = super(IndexedField, self).__set__(instance, value)
        instance._set_index('{}_bin'.format(self.fname), value)
        return value

    def _filter(self, startkey, endkey=None, **kwargs):
        if isinstance(startkey, self._type) and self._type not in self._simple_types:
            startkey = self._type.to_simple(startkey)
        if isinstance(endkey, self._type) and self._type not in self._simple_types:
            endkey = self._type.to_simple(endkey)
        kwargs.setdefault('max_results', 1000000)
        res = self._declared_in._get_index('{}_bin'.format(self.fname),
                                           startkey=startkey,
                                           endkey=endkey,
                                           **kwargs).results
        return res

    def filter(self, *args, **kwargs):
        kwargs['return_terms'] = False
        res = self._filter(*args, **kwargs)
        return set(res)


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
        return self._instance._data_container[self.fname][name]

    def __getitem__(self, name):
        return self._get_field_val(name)

    def __setitem__(self, name, value):
        inst = self._instance
        inst._add_index('%s_bin' % self.fname, '{}|{}'.format(name, value))

    def __delitem__(self, name):
        inst = self._instance
        del inst._data_container[self.fname][name]
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
        instance._data_container[self.fname] = self.default
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

    _defined_models = set()

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


        cls._model_fields = [getattr(cls, x) for x in model_fields]

        if bases == (object, ):
            return cls

        cls.bucket = Replacer('bucket', get_bucket, mcs)
        mcs._defined_models.add(cls)
        return cls


    @classmethod
    def setup(mcs, riak_client):
        mcs.riak_client = riak_client

    @classmethod
    def session_end(mcs, result=True):
        for cls in mcs._defined_models:
            for to_save in cls._c.lazy_save:
                try:
                    to_save.save()
                except DBLayerException:
                    continue
            cls._c.lazy_save.clear()
        mcs.riak_client.session_end(result)

    @classmethod
    def session_start(mcs):
        clear_cache()
        mcs.riak_client.session_start()


class NestedField(FieldBase):

    def __init__(self, _class, fname=None, default=NONE, hash_key=None):
        self._class = _class
        self._hash_key = hash_key
        super(NestedField, self).__init__(fname=fname, default=default)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        cached = getattr(instance, '_real_obj_%s' % self.fname, None)
        if cached:
            return cached
        if self._hash_key is not None:
            obj = NestedModelHash(self, instance, self._class, self._hash_key)
        else:
            obj = self._class(self, instance)
        setattr(instance, '_real_obj_%s' % self.fname, obj)
        return obj

    def __set__(self, instance, value):
        obj = getattr(instance, self.fname)
        obj.from_dict(value)

    def __delete__(self, instance):
        obj = getattr(instance, self.fname)
        obj.delete()


class NestedModel(object):

    __metaclass__ = ModelMeta

    _nested_value = None

    def __init__(self, field, parent):
        self._field = field
        self._parent = parent

    def from_dict(self, data):
        for field in self._model_fields:
            fname = field.fname
            gname = field.gname
            val = data.get(fname, NONE)
            default = field.default
            if val is NONE and default is not NONE:
                setattr(self, gname, default)
            elif val is not NONE:
                setattr(self, gname, val)
        return

    @property
    def _data_container(self):
        pdc = self._parent._data_container
        try:
            ppdc = pdc[self._field.fname]
        except KeyError:
            ppdc = pdc[self._field.fname] = {}
        if self._field._hash_key is None:
            return ppdc
        else:
            try:
                ret = ppdc[self._nested_value]
            except KeyError:
                ret = ppdc[self._nested_value] = {}
            return ret

    def _field_changed(self, field):
        return self._parent._modified_fields.add(self._field.fname)

    def delete(self):
        if self._field._hash_key is None:
            del self._parent._data_container[self._field.fname]



class NestedModelHash(object):

    def __init__(self, field, parent, _class, hash_key):
        self._field = field
        self._parent = parent
        self._class = _class
        self._hash_key = hash_key
        self._cache = {}

    def __getitem__(self, name):
        try:
            return self._cache[name]
        except KeyError:
            obj = self._class(self._field, self._parent)
            obj._nested_value = name
            self._cache[name] = obj
            return obj

    def __setitem__(self, name, value):
        obj = self[name]
        return obj.from_dict(value)

    def __delitem__(self, name):
        obj = self[name]
        obj.delete()
        del self._cache[name]

    def from_dict(self, data):
        hk = data[self._hash_key]
        self[hk] = data



class Model(object):

    __metaclass__ = ModelMeta

    _c = ClassCache()

    _key = None
    _new = None
    _real_riak_object = None

    _changed = False

    def __init__(self, key=None):
        self._modified_fields = set()
        # TODO: that _indexes_changed should be smarter
        self._indexes_changed = False
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


    @property
    def _data_container(self):
        return self._riak_object.data

    @changes_state_for('index')
    def _set_index(self, name, value):
        self._indexes_changed = True
        return self._riak_object.set_index(name, value)

    @changes_state_for('index')
    def _add_index(self, *args, **kwargs):
        self._indexes_changed = True
        return self._riak_object.add_index(*args, **kwargs)

    @changes_state_for('index')
    def _remove_index(self, *args, **kwargs):
        self._indexes_changed = True
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

    def _field_changed(self, field):
        self._modified_fields.add(field.fname)

    def changed(self):
        if self._modified_fields:
            return True
        return self._indexes_changed

    def to_dict(self):
        return dict(self._riak_object.data)

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

    def __hash__(self):
        return hash(self.key)

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

    @classmethod
    def multi_get(cls, keys):
        # TODO: parallel execution
        ret = map(cls.get, keys)
        return ret

    def _reset_state(self):
        self._new = False
        self._modified_fields.clear()
        self._indexes_hash = None

    @clears_state_for('index')
    def save(self, force=False):
        if self.changed() or force or self._new:
            res = self._riak_object.store()
            self._reset_state()
            return res
        else:
            raise DBLayerException("No changes")

    def save_lazy(self):
        self._c.lazy_save.add(self)

    def delete(self):
        ls = self._c.lazy_save
        try:
            ls.remove(self.key)
        except KeyError:
            pass
        raise NotImplementedError()
