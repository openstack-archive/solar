# -*- coding: utf-8 -*-
# msgpack is way faster but less readable
# using json for easier debug
import json
import sys
import uuid

from peewee import BlobField
from peewee import CharField
from peewee import ForeignKeyField
from peewee import Model
from solar.dblayer.model import clear_cache
from threading import RLock

encoder = json.dumps


def wrapped_loads(data, *args, **kwargs):
    if not isinstance(data, basestring):
        data = str(data)
    return json.loads(data, *args, **kwargs)


decoder = wrapped_loads


class _DataField(BlobField):
    def db_value(self, value):
        return super(_DataField, self).db_value(encoder(value))

    def python_value(self, value):
        return decoder(super(_DataField, self).python_value(value))


class _LinksField(_DataField):
    def db_value(self, value):
        return super(_LinksField, self).db_value(list(value))

    def python_value(self, value):
        ret = super(_LinksField, self).python_value(value)
        return [tuple(e) for e in ret]


class _SqlBucket(Model):
    def __init__(self, *args, **kwargs):
        self._new = kwargs.pop('_new', False)
        ed = kwargs.pop('encoded_data', None)
        if ed:
            self.encoded_data = ed
        if 'data' not in kwargs:
            kwargs['data'] = {}
        super(_SqlBucket, self).__init__(*args, **kwargs)

    key = CharField(primary_key=True, null=False)
    data = _DataField(null=False)
    vclock = CharField(max_length=32, null=False)
    links = _LinksField(null=False, default=list)

    @property
    def encoded_data(self):
        return self.data.get('_encoded_data')

    @encoded_data.setter
    def encoded_data(self, value):
        self.data['_encoded_data'] = value

    def save(self, force_insert=False, only=None):
        if self._new:
            force_insert = True
            self._new = False
        ret = super(_SqlBucket, self).save(force_insert, only)
        return ret

    @property
    def sql_session(self):
        return self.bucket.sql_session


class FieldWrp(object):
    def __init__(self, name):
        self.name = name

    def __get__(self, instance, owner):
        return getattr(instance._sql_bucket_obj, self.name)

    def __set__(self, instance, value):
        setattr(instance._sql_bucket_obj, self.name, value)


class _SqlIdx(Model):
    name = CharField(null=False, index=True)
    value = CharField(null=False, index=True)


class RiakObj(object):
    key = FieldWrp('key')
    data = FieldWrp('data')
    vclock = FieldWrp('vclock')
    links = FieldWrp('links')
    encoded_data = FieldWrp('encoded_data')

    def __init__(self, sql_bucket_obj, new=False):
        self._sql_bucket_obj = sql_bucket_obj
        self.new = sql_bucket_obj._new
        self.fetch_indexes()

    @property
    def sql_session(self):
        return self._sql_bucket_obj.sql_session

    @property
    def bucket(self):
        return self._sql_bucket_obj.bucket

    @property
    def indexes(self):
        self.fetch_indexes()
        return self._indexes

    def fetch_indexes(self):
        if not hasattr(self, '_indexes'):
            idxes = self.bucket._sql_idx.select().where(
                self.bucket._sql_idx.key == self.key)
            self._indexes = set((idx.name, idx.value) for idx in idxes)

    @indexes.setter
    def indexes(self, value):
        assert isinstance(value, set)
        self._indexes = value

    def _save_indexes(self):
        # TODO:  possible optimization
        # update only what's needed
        # don't delete all at first
        q = self.bucket._sql_idx.delete().where(self.bucket._sql_idx.key ==
                                                self.key)
        q.execute()

        for iname, ival in self.indexes:
            idx = self.bucket._sql_idx(key=self.key, name=iname, value=ival)
            idx.save()

    def add_index(self, field, value):
        self.indexes.add((field, value))
        return self

    def set_index(self, field, value):
        to_rem = set((x for x in self.indexes if x[0] == field))
        self.indexes.difference_update(to_rem)
        return self.add_index(field, value)

    def remove_index(self, field=None, value=None):
        if field is None and value is None:
            # q = self.bucket._sql_idx.delete().where(
            #     self.bucket._sql_idx.key == self.key)
            # q.execute()
            self.indexes.clear()
        elif field is not None and value is None:
            # q = self.bucket._sql_idx.delete().where(
            #     (self.bucket._sql_idx.key == self.key) &
            #     (self.bucket._sql_idx.name == field))
            # q.execute()
            to_rem = set((x for x in self.indexes if x[0] == field))
            self.indexes.difference_update(to_rem)
        elif field is not None and value is not None:
            # q = self.bucket._sql_idx.delete().where(
            #     (self.bucket._sql_idx.key == self.key) &
            #     (self.bucket._sql_idx.name == field) &
            #     (self.bucket._sql_idx.value == value))
            # q.execute()
            to_rem = set((
                x for x in self.indexes if x[0] == field and x[1] == value))
            self.indexes.difference_update(to_rem)
        return self

    def store(self, return_body=True):
        self.vclock = uuid.uuid4().hex
        assert self._sql_bucket_obj is not None
        self._sql_bucket_obj.save()
        self._save_indexes()
        return self

    def delete(self):
        self._sql_bucket_obj.delete()
        return self

    @property
    def exists(self):
        return not self.new

    def get_link(self, tag):
        return next(x[1] for x in self.links if x[2] == tag)

    def set_link(self, obj, tag=None):
        if isinstance(obj, tuple):
            newlink = obj
        else:
            newlink = (obj.bucket.name, obj.key, tag)

        multi = [x for x in self.links if x[0:1] == newlink[0:1]]
        for item in multi:
            self.links.remove(item)

        self.links.append(newlink)
        return self

    def del_link(self, obj=None, tag=None):
        assert obj is not None or tag is not None
        if tag is not None:
            links = [x for x in self.links if x[2] != tag]
        else:
            links = self.links
        if obj is not None:
            if not isinstance(obj, tuple):
                obj = (obj.bucket.name, obj.key, tag)
            links = [x for x in links if x[0:1] == obj[0:1]]
        self.links = links
        return self


class IndexPage(object):
    def __init__(self, index, results, return_terms, max_results,
                 continuation):
        self.max_results = max_results
        self.index = index
        if not return_terms:
            self.results = tuple(x[0] for x in results)
        else:
            self.results = tuple(results)

        if not max_results or not self.results:
            self.continuation = None
        else:
            self.continuation = str(continuation + len(self.results))
        self.return_terms = return_terms

    def __len__(self):
        return len(self.results)

    def __getitem__(self, item):
        return self.results[item]


class Bucket(object):
    def __init__(self, name, client):
        self.client = client
        table_name = "bucket_%s" % name.lower()
        self.name = table_name
        idx_table_name = 'idx_%s' % name.lower()

        class ModelMeta(object):
            db_table = table_name
            database = self.client.sql_session

        self._sql_model = type(table_name, (_SqlBucket, ), {'Meta': ModelMeta,
                                                            'bucket': self})
        _idx_key = ForeignKeyField(self._sql_model, null=False, index=True)

        class IdxMeta(object):
            db_table = idx_table_name
            database = self.client.sql_session

        self._sql_idx = type(idx_table_name, (_SqlIdx, ), {'Meta': IdxMeta,
                                                           'bucket': self,
                                                           'key': _idx_key})

    def search(self, q, rows=10, start=0, sort=''):
        raise NotImplementedError()

    def create_search(self, index):
        raise NotImplementedError()

    def set_property(self, name, value):
        return

    def get_properties(self):
        return {'search_index': False}

    def get(self, key):
        try:
            ret = self._sql_model.get(self._sql_model.key == key)
        except self._sql_model.DoesNotExist:
            ret = None
        new = ret is None
        if new:
            ret = self._sql_model(key=key, _new=new)
        return RiakObj(ret, new)

    def delete(self, data, *args, **kwargs):
        if isinstance(data, basestring):
            key = data
        else:
            key = data.key
        self._sql_model.delete().where(self._sql_model.key == key).execute()
        self._sql_idx.delete().where(self._sql_idx.key == key).execute()
        return self

    def new(self, key, data=None, encoded_data=None, **kwargs):
        if key is not None:
            try:
                ret = self._sql_model.get(self._sql_model.key == key)
            except self._sql_model.DoesNotExist:
                ret = None
            new = ret is None
        else:
            key = uuid.uuid4().hex
            new = True
        if new:
            ret = self._sql_model(key=key, _new=new)
        ret.key = key
        ret.data = data if data is not None else {}
        if encoded_data:
            ret.encoded_data = encoded_data
        ret.links = []
        ret.vclock = "new"
        return RiakObj(ret, new)

    def get_index(self,
                  index,
                  startkey,
                  endkey=None,
                  return_terms=None,
                  max_results=None,
                  continuation=None,
                  timeout=None,
                  fmt=None,
                  term_regex=None):
        if startkey and endkey is None:
            endkey = startkey
        if startkey > endkey:
            startkey, endkey = endkey, startkey

        if index == '$key':
            if return_terms:
                q = self._sql_model.select(self._sql_model.value,
                                           self._sql_model.key)
            else:
                q = self._sql_model.select(self._sql_model.key)
            q = q.where(
                self._sql_model.key >= startkey,
                self._sql_model.key <= endkey).order_by(self._sql_model.key)
        elif index == '$bucket':
            if return_terms:
                q = self._sql_model.select(self._sql_model.value,
                                           self._sql_model.key)
            else:
                q = self._sql_model.select(self._sql_model.key)
            if not startkey == '_' and endkey == '_':
                q = q.where(self._sql_model.key >= startkey,
                            self._sql_model.key <= endkey)
        else:
            if return_terms:
                q = self._sql_idx.select(self._sql_idx.value,
                                         self._sql_idx.key)
            else:
                q = self._sql_idx.select(self._sql_idx.key)
            q = q.where(
                self._sql_idx.name == index, self._sql_idx.value >= startkey,
                self._sql_idx.value <= endkey).order_by(self._sql_idx.value)

        max_results = int(max_results or 0)
        continuation = int(continuation or 0)
        if max_results:
            q = q.limit(max_results)
        if continuation:
            q = q.offset(continuation)

        q = q.tuples()

        return IndexPage(index, q, return_terms, max_results, continuation)

    def multiget(self, keys):
        if not keys:
            return []
        else:
            q = self._sql_model.select().where(self._sql_model.key << list(
                keys))
            return map(RiakObj, list(q))

    @property
    def sql_session(self):
        return self.client.sql_session


class SqlClient(object):
    block = RLock()

    search_dir = None

    def __init__(self, *args, **kwargs):
        db_class_str = kwargs.pop("db_class", 'SqliteDatabase')
        try:
            mod, fromlist = db_class_str.split('.')
        except ValueError:
            mod = 'peewee'
            fromlist = db_class_str
        __import__(mod, fromlist=[fromlist])
        db_class = getattr(sys.modules[mod], fromlist)
        session = db_class(*args, **kwargs)
        self._sql_session = session
        self.buckets = {}

    def bucket(self, name):
        with self.block:
            if name not in self.buckets:
                b = Bucket(name, self)
                b._sql_model.create_table(fail_silently=True)
                b._sql_idx.create_table(fail_silently=True)
                self.buckets[name] = b
            return self.buckets[name]

    @property
    def sql_session(self):
        return self._sql_session

    def session_start(self):
        clear_cache()
        sess = self._sql_session
        sess.begin()

    def session_end(self, result=True):
        sess = self._sql_session
        if result:
            sess.commit()
        else:
            sess.rollback()
        clear_cache()

    def delete_all(self, cls):
        # naive way for SQL, we could delete whole table contents
        rst = cls.bucket.get_index('$bucket',
                                   startkey='_',
                                   max_results=100000).results
        for key in rst:
            cls.bucket.delete(key)
