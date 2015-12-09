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

from collections import Counter
from operator import itemgetter
from solar.dblayer.proxy import DBLayerProxy

from threading import RLock


class LFUCache(object):

    def __init__(self, owner, maxsize):
        self._maxsize = maxsize
        self._store = {}
        self._lock = RLock()
        self._use_count = Counter()
        self._owner = owner

    def set(self, item, value):
        with self._lock:
            if item in self._store:
                self._use_count[item] += 1
                return self._store[item]
            store_len = len(self._store)
            if store_len >= self._maxsize:
                deleted = 0
                # overflow + one more
                exp_deleted = (store_len - self._maxsize) + 1
                for k, _ in sorted(self._use_count.iteritems(),
                                   key=itemgetter(1)):
                    if self.is_deletable(self._store[k]):
                        del self[k]
                        deleted += 1
                    if deleted == exp_deleted:
                        break
            self._use_count[item] += 1
            self._store[item] = value
            return value

    def is_empty(self):
        return False if self._store else True

    def get(self, item):
        obj = self._store[item]
        return DBLayerProxy(obj)

    def __eq__(self, other):
        if isinstance(other, dict):
            for k, v in other.iteritems():
                if k not in self._store:
                    return False
                mv = self._store[k]
                if not v == mv:
                    return False
            return True
        else:
            return self == other

    def __setitem__(self, item, value):
        self.set(item, value)

    def is_deletable(self, elem):
        if elem.changed():
            return False
        if elem in elem._c.lazy_save:
            return False
        if elem._c.refs[elem.key]:
            return False
        return True

    def __contains__(self, item):
        return self._store.__contains__(item)

    def __delitem__(self, item):
        with self._lock:
            del self._store[item]
            del self._use_count[item]

    def __getitem__(self, item):
        # print 'incrementing in cache', item
        with self._lock:
            res = self._store[item]  # will crash when no key but it's ok
            self._use_count[item] += 1
        return res

    def incr_count(self, item):
        with self._lock:
            if item in self._use_count:
                self._use_count[item] += 1
