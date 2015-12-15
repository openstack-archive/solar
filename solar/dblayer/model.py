#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from functools import total_ordering
from functools import wraps

import time
import uuid
import weakref

from collections import defaultdict
from random import getrandbits
from threading import RLock

from solar.dblayer.conflict_resolution import dblayer_conflict_resolver
from solar.dblayer.lfu_cache import LFUCache
from solar.utils import get_local


class DBLayerException(Exception):
    pass


class DBLayerNotFound(DBLayerException):
    pass


class DBLayerNoRiakObj(DBLayerException):
    pass


class NONE(object):
    """A None like type"""


class SingleIndexCache(object):
    def __init__(self):
        self.lock = RLock()
        self.cached_vals = []

    def __enter__(self):
        self.lock.acquire()
        return self

    def fill(self, values):
        self.cached_vals = values

    def wipe(self):
        self.cached_vals = []

    def get_index(self, real_funct, ind_name, **kwargs):
        kwargs.setdefault('max_results', 999999)
        if not self.cached_vals:
            recvs = real_funct(ind_name, **kwargs).results
            self.fill(recvs)

    def filter(self, startkey, endkey, max_results=1):
        c = self.cached_vals
        for (curr_val, obj_key) in c:
            if max_results == 0:
                break
            if curr_val >= startkey:
                if curr_val <= endkey:
                    max_results -= 1
                    yield (curr_val, obj_key)
                else:
                    break

    def __exit__(self, *args, **kwargs):
        self.lock.release()


class SingleClassCache(object):

    __slots__ = ['obj_cache', 'db_ch_state',
                 'lazy_save', 'origin_class',
                 'refs']

    def __init__(self, origin_class):
        self.obj_cache = LFUCache(origin_class, 200)
        self.db_ch_state = {'index': set()}
        self.lazy_save = set()
        self.refs = defaultdict(weakref.WeakSet)
        self.origin_class = origin_class


class ClassCache(object):
    def __init__(self, *args, **kwargs):
        self._l = RLock()

    def __get__(self, inst, owner):
        # th = current_thread()
        with self._l:
            l = Model._local
            # better don't duplicate class names
            cache_name = owner.__name__
            try:
                cache_id = l.cache_id
            except AttributeError:
                cache_id = uuid.UUID(int=getrandbits(128), version=4).hex
                setattr(l, 'cache_id', cache_id)
            if getattr(l, 'cache_id_cmp', None) != cache_id:
                # new cache
                setattr(l, 'cache_id_cmp', cache_id)
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
    # th = current_thread()
    l = Model._local
    cache_id = uuid.UUID(int=getrandbits(128), version=4).hex
    setattr(l, 'cache_id_cmp', cache_id)


def get_bucket(_, owner, mcs):
    name = owner.get_bucket_name()
    bucket = mcs.riak_client.bucket(name)
    bucket.resolver = dblayer_conflict_resolver
    return bucket


def changes_state_for(_type):
    def _inner1(f):
        @wraps(f)
        def _inner2(obj, *args, **kwargs):
            obj._c.db_ch_state['index'].add(obj.key)
            obj.save_lazy()
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
    with obj._lock:
        state = obj._c.db_ch_state.get(_type)
        if state:
            if True:
                # TODO: solve it
                obj.save_all_lazy()
                state = obj._c.db_ch_state.get(_type)
                if not state:
                    return
            raise Exception("Dirty state, save all %r objects first" %
                            obj.__class__)


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
    def greater(cls, inst):
        if isinstance(inst, cls):
            return cls(inst._val + 'g')
        return cls(inst + 'g')

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
            v -= int('9' * cls.format_size)
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
        if isinstance(other, basestring):
            first_ch = other[0]
            if first_ch not in (self.positive_char, self.negative_char):
                raise Exception("Cannot compare %r with %r" % (self, other))
            else:
                other = self.from_simple(other)
        if not isinstance(other, self.__class__):
            raise Exception("Cannot compare %r with %r" % (self, other))
        so = other._val[0]
        ss = self._val[0]
        son = so == other.negative_char
        ssn = ss == self.negative_char
        if son != ssn:
            return False
        return self._val[1:] == other._val[1:]

    def __gt__(self, other):
        if isinstance(other, basestring):
            first_ch = other[0]
            if first_ch not in (self.positive_char, self.negative_char):
                raise Exception("Cannot compare %r with %r" % (self, other))
            else:
                other = self.from_simple(other)
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

    # in from_dict, when you set value to None,
    # then types that are *not* there are set to NONE
    _not_nullable_types = {int, float, long, str, unicode, basestring}
    _simple_types = {int, float, long, str, unicode, basestring, list, tuple,
                     dict}

    def __init__(self, _type, fname=None, default=NONE):
        if _type == str:
            _type = basestring
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
            raise Exception("Invalid type %r for %r, expected %r" %
                            (type(value), self.fname, self._type))
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
        if isinstance(startkey,
                      self._type) and self._type not in self._simple_types:
            startkey = self._type.to_simple(startkey)
        if isinstance(endkey,
                      self._type) and self._type not in self._simple_types:
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
        return res


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
        return list(res)


class CompositeIndexFieldWrp(IndexFieldWrp):
    def reset(self):
        index = []
        for f in self._field_obj.fields:
            index.append(self._instance._data_container.get(f, ''))
        index = '|'.join(index)

        index_to_del = []
        for index_name, index_val in self._instance._riak_object.indexes:
            if index_name == '%s_bin' % self.fname:
                if index != index_val:
                    index_to_del.append((index_name, index_val))

        for index_name, index_val in index_to_del:
            self._instance._remove_index(index_name, index_val)

        self._instance._add_index('%s_bin' % self.fname, index)


class CompositeIndexField(IndexField):

    _wrp_class = CompositeIndexFieldWrp

    def __init__(self, fields=(), *args, **kwargs):
        super(CompositeIndexField, self).__init__(*args, **kwargs)
        self.fields = fields

    def _parse_key(self, startkey):
        vals = [startkey[f] for f in self.fields if f in startkey]
        return '|'.join(vals) + '*'


class ModelMeta(type):

    _defined_models = set()

    def __new__(mcs, name, bases, attrs):
        cls = super(ModelMeta, mcs).__new__(mcs, name, bases, attrs)
        model_fields = set((name
                            for (name, attr) in attrs.items()
                            if isinstance(attr, FieldBase) and
                            not name.startswith('_')))
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
                model_fields_base = base._model_fields
            except AttributeError:
                continue
            else:
                for given in model_fields_base:
                    model_fields.add(given)

        cls._model_fields = [getattr(cls, x) for x in model_fields]

        if bases == (object, ):
            return cls

        if issubclass(cls, NestedModel):
            return cls

        cls.bucket = Replacer('bucket', get_bucket, mcs)
        mcs._defined_models.add(cls)
        return cls

    @classmethod
    def setup(mcs, riak_client):
        if hasattr(mcs, 'riak_client'):
            raise DBLayerException("Setup already done")
        mcs.riak_client = riak_client

    @classmethod
    def remove_all(mcs):
        for model in mcs._defined_models:
            model.delete_all()

    @classmethod
    def save_all_lazy(mcs, result=True):
        for cls in mcs._defined_models:
            for to_save in cls._c.lazy_save:
                try:
                    to_save.save()
                except DBLayerException:
                    continue
            cls._c.lazy_save.clear()

    @classmethod
    def session_end(mcs, result=True):
        mcs.save_all_lazy()
        mcs.riak_client.session_end(result)

    @classmethod
    def session_start(mcs):
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

    _local = get_local()()

    _lock = RLock()  # for class objs

    def __init__(self, key=None):
        self._modified_fields = set()
        # TODO: that _indexes_changed should be smarter
        self._indexes_changed = False
        self.key = key
        self._lock = RLock()

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
        d = dict(self._riak_object.data)
        d['key'] = self.key
        return d

    def __str__(self):
        if self._riak_object is None:
            return "<%s not initialized>" % (self.__class__.__name__)
        return "<%s %s:%s>" % (self.__class__.__name__,
                               self._riak_object.bucket.name, self.key)

    def __hash__(self):
        return hash(self.key)

    @classmethod
    def new(cls, key, data):
        return cls.from_dict(key, data)

    @classmethod
    def get_or_create(cls, key):
        try:
            return cls.get(key)
        except DBLayerNotFound:
            return cls.new(key, {})

    @classmethod
    def from_riakobj(cls, riak_obj):
        obj = cls(riak_obj.key)
        obj._riak_object = riak_obj
        if obj._new is None:
            obj._new = False
        cache = cls._c.obj_cache
        cache.set(riak_obj.key, obj)
        # cache may adjust object
        return cache.get(riak_obj.key)

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
        # shouldn't be needed, but may cover some weird usecase
        # when inproperly using from_dict, because it then leads to conflicts
        if key in cls._c.obj_cache:
            raise DBLayerException("Object already exists in cache"
                                   " cannot create second")
        data['key'] = key

        with cls._c.obj_cache._lock:
            if key in cls._c.obj_cache:
                return cls._c.obj_cache.get(key)
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
            if val is None and field._type not in field._not_nullable_types:
                val = NONE
            if val is NONE and default is not NONE:
                setattr(obj, gname, default)
            elif val is not NONE:
                setattr(obj, gname, val)
        return obj

    @classmethod
    def get(cls, key):
        try:
            return cls._c.obj_cache.get(key)
        except KeyError:
            riak_object = cls.bucket.get(key)
            if not riak_object.exists:
                raise DBLayerNotFound(key)
            else:
                return cls.from_riakobj(riak_object)

    @classmethod
    def multi_get(cls, keys):
        # TODO: parallel execution
        ret = map(cls.get, keys)
        return ret

    def _reset_state(self):
        self._new = False
        self._modified_fields.clear()
        self._indexes_changed = False

    @classmethod
    def save_all_lazy(cls):
        for to_save in set(cls._c.lazy_save):
            try:
                to_save.save()
            except DBLayerException:
                continue
        cls._c.lazy_save.clear()

    @clears_state_for('index')
    def save(self, force=False):
        with self._lock:
            if self.changed() or force or self._new:
                res = self._riak_object.store()
                self._reset_state()
                return res
            else:
                raise DBLayerException("No changes")

    def save_lazy(self):
        self._c.lazy_save.add(self)

    @classmethod
    def delete_all(cls):
        cls.riak_client.delete_all(cls)

    def delete(self):
        ls = self._c.lazy_save
        try:
            ls.remove(self)
        except KeyError:
            pass
        try:
            del self._c.obj_cache[self.key]
        except KeyError:
            pass
        self._riak_object.delete()
        return self
