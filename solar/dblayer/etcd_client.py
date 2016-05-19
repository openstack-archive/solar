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
#
# A short explanation of the architecture for the database:
# Because etcd doesn't support secondary indexes like Riak,
# We need to emulate them. We keep two types of KV in the database
# *Bucket keys*
# "bck/{bucket_name}/{model_key}" -> data
# These keys are used to retrieve models by name
# *Index keys*
# "idx/{bucket_name}/{field_name}/{value}/{uuid}" -> model_key
# These keys are used to retrieve model keys by indexed value

import json
import uuid
from threading import RLock

from etcd.etcdserver.etcdserverpb import rpc_pb2
from .mini_grpc import Grpc

from solar.dblayer.model import clear_cache


class KeyNotFound(Exception):
    """Raised when a query for a single key in etcd returned no data"""


class RiakObj(object):
    def __init__(self, *args, **kwargs):
        self.new = kwargs.pop('new', False)
        self.key = kwargs.pop('key')
        self.data = kwargs.pop('data', {})
        self._idx_keys = self.data.pop('_idx_keys', [])
        self.vclock = self.data.pop('vclock', uuid.uuid4().hex)
        self.bucket = kwargs.pop('bucket')
        self._indexes = None  # Lazy

    def delete(self):
        self.bucket.delete(self)
        return self

    @property
    def exists(self):
        return not self.new

    @property
    def indexes(self):
        if self._indexes is None:
            self._fetch_indexes()
        return self._indexes

    @indexes.setter
    def indexes(self, value):
        self._indexes = value

    def serialize(self):
        data = self.data.copy()
        data.update({
            'key': self.key,
            '_idx_keys': self._idx_keys,
            'vclock': self.vclock,
        })
        return json.dumps(data)

    def store(self, **kwargs):
        self.vclock = self.vclock or uuid.uuid4().hex
        self._save_indexes()
        self.bucket.save(self)
        return self

    def _save_indexes(self):
        self.bucket.client.to_delete += self._idx_keys
        idx_keys = [(
            'idx\0{}\0{}\0{}\0{}'.format(
                self.bucket.name,
                field,
                value,
                uuid.uuid4().hex
            ),
            self.key,
        ) for field, value in self.indexes]
        self.bucket.client.to_set.update(idx_keys)
        self._idx_keys = [k for k, v in idx_keys]

    def _fetch_indexes(self):
        self._indexes = set()
        for idx_key in self._idx_keys:
            key  = self.client.get_key(idx_key)
            value = idx_key.split('\0')[3]
            self._indexes.add((key, value))

    def add_index(self, field, value):
        self.indexes.add((field, value))
        return self

    def set_index(self, field, value):
        self.indexes -= {(k, v) for (k, v) in self.indexes if k == field}
        return self.add_index(field, value)

    def remove_index(self, field=None, value=None):
        if field is None and value is None:
            self.indexes.clear()
        elif value is None:
            self.indexes -= {(k, v) for (k, v) in self.indexes if k == field}
        else:
            self.indexes.discard((field, value))


class IndexPage(object):
    def __init__(self, index, results, return_terms, max_results,
                 continuation):
        self.max_results = max_results
        self.index = index
        if not return_terms:
            self.results = list(x[0] for x in results)
        else:
            self.results = list(results)

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

    lock = RLock()

    def __init__(self, name, client):
        self.client = client
        self.name = name

    def delete(self, object_):
        self.client.to_delete +=\
            [self.format_key(object_.key)] + object_._idx_keys
        self.client.commit()
        return self

    def new(self, key, data=None, encoded_data=None, **kwargs):
        if key is not None:
            try:
                data = json.loads(
                    self.client.get_key(self.format_key(key))
                )
            except KeyNotFound:
                data = data
            new = data is None
        else:
            key = uuid.uuid4().hex
            new = True
        if new:
            data = {}
        data['key'] = key
        data['new'] = new
        data['bucket'] = self
        return RiakObj(new, **data)

    def save(self, object_):
        data = object_.serialize()
        self.client.to_set[self.format_key(object_.key)] = data
        self.client.commit()

    def set_property(self, name, value):
        """Required for complience with riak bucket."""

    def get_properties(self):
        """Required for complience with riak bucket."""
        return {'search_index': False}

    def set_properties(self, properties):
        """Required for complience with riak bucket."""

    def format_key(self, key):
        return 'bck\0{}\0{}'.format(self.name, key)

    def format_idx_range(self, field_name, start_value, end_value):
        return (
            'idx\0{}\0{}\0{}'.format(self.name, field_name, start_value),
            'idx\0{}\0{}\0{}'.format(self.name, field_name, end_value),
        )

    def get(self, key):
        try:
            data = json.loads(self.client.get_key(self.format_key(key)))
        except KeyNotFound:
            data = {}
            new = True
        else:
            new = False

        return RiakObj(key=key, new=new, bucket=self, data=data)

    def get_index(
        self,
        index,
        startkey,
        endkey=None,
        return_terms=None,
        max_results=None,
        continuation=None,
        timeout=None,
        fmt=None,
        term_regex=None,
    ):
        if term_regex:
            raise NotImplementedError('Cannot search by regex')
        if startkey > endkey:
            startkey, endkey = endkey, startkey
        if index == '$key':
            data = self.client.get_range(
                self.format_key(startkey),
                self.format_key(endkey),
                return_terms
            )
        elif index == '$bucket':
            data = self.client.get_range(
                self.format_key(startkey),
                self.format_key(endkey),
                return_terms,
            )
        else:
            data = self.client.get_range(
                *self.format_idx_range(index, startkey, endkey),
                return_terms=return_terms
            )
        max_results = int(max_results or 0)
        continuation = int(continuation or 0)
        return IndexPage(index, data, return_terms, max_results, continuation)


class EtcdClient(object):
    lock = RLock()

    def __init__(self, host, port, *args, **kwargs):
        self.grpc = Grpc(host, port)
        self.to_set = {}
        self.to_delete = []
        self.buckets = {}

    def bucket(self, name):
        with self.lock:
            if name in self.buckets:
                return self.buckets[name]
            return Bucket(name, self)

    def session_start(self):
        clear_cache()

    def session_end(self, result=True):
        if result:
            self.commit()
        else:
            self.rollback()
        clear_cache()

    def clear_uncommited(self):
        self.to_set.clear()
        del self.to_delete[:]

    def rollback(self):
        self.clear_uncommited()

    def commit(self):
        requests = [rpc_pb2.RequestUnion(
            request_delete_range=rpc_pb2.DeleteRangeRequest(key=key)
        ) for key in self.to_delete]
        requests += [
            rpc_pb2.RequestUnion(
                request_put=rpc_pb2.PutRequest(key=key, value=value)
            )
            for key, value in self.to_set.items()
        ]
        if requests:
            resp = self.grpc.request(
                'POST',
                '/etcdserverpb.KV/Txn',
                rpc_pb2.TxnRequest(success=requests),
                rpc_pb2.TxnResponse,
                3,
            )
            self.clear_uncommited()

    def get_key(self, key):
        request = rpc_pb2.RangeRequest(key=key)
        resp = self.grpc.request(
            'PUT',
            '/etcdserverpb.KV/Range',
            request,
            rpc_pb2.RangeResponse,
            2,
        )
        if resp.kvs:
            return resp.kvs[0].value
        else:
            raise KeyNotFound('Key {} not found'.format(key))

    def get_range(self, key, range_end, return_terms):
        request = rpc_pb2.RangeRequest(key=key, range_end=range_end)
        resp = self.grpc.request(
            'PUT',
            '/etcdserverpb.KV/Range',
            request,
            rpc_pb2.RangeResponse,
            2,
        )
        if return_terms:
            return [(kv.value, kv.key) for kv in resp.kvs]
        else:
            return [(kv.value,) for kv in resp.kvs]
