from heapq import nsmallest
from operator import itemgetter
from collections import defaultdict, Counter
from solar.dblayer.proxy import DBLayerProxy
import gc
import sys

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
                exp_deleted = (store_len - self._maxsize) + 1  # overflow + one more
                for k, _ in sorted(self._use_count.iteritems(), key=itemgetter(1)):
                    if self.is_deletable(self._store[k]):
                        del self[k]
                        deleted += 1
                    if deleted == exp_deleted:
                        break
            self._use_count[item] += 1
            self._store[item] = value
            return value

    def get(self, item):
        obj = self._store[item]
        return DBLayerProxy(obj)

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
