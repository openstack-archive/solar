# -*- coding: utf-8 -*-
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

import gevent

from collections import deque
from gevent.lock import RLock
from gevent.lock import Semaphore


class FakeLock(object):
    """A lock that does not lock, used to replace peewee connection lock"""

    def acquire(self, *args, **kwargs):
        return True

    def release(self, *args, **kwargs):
        return True

    def __enter__(self):
        return True

    def __exit__(self, *args, **kwargs):
        return True

    def __repr__(self):
        return "<%s at 0x%x>" % (self.__class__.__name__, id(self))


def get_pooled_db(orig_db, pool_size, pool_overflow):
    """Wrapper that makes enables pool in DB

This is wrapper for peewee database that has separate own logic of
connection pooling, adjusted for our use case
"""
    db_lock = RLock()
    pool = deque()
    pool_size_overflow = pool_size + pool_overflow

    _tmp_lock = RLock()
    _conn_count = [0, 0, 0]
    s = Semaphore(pool_size_overflow)

    def close_conn(g):
        g._db_obj._close(g._db_conn)

    def pooled__connect(obj, *args, **kwargs):
        ret = None
        n = 10
        max_tries = n - 1
        for i in xrange(n):
            if not s.acquire(blocking=True, timeout=0.1):
                continue
            try:
                try:
                    ret = pool.pop()
                    c = ret.cursor()
                    try:
                        c.execute('SELECT 1;')
                    finally:
                        c.close()
                except IndexError:
                    with _tmp_lock:
                        _conn_count[0] += 1
                        _conn_count[1] += 1
                    ret = obj._orig__connect(*args, **kwargs)
            except Exception:
                s.release()
                if i == max_tries:
                    raise
            else:
                if ret is not None:
                    break
        if ret is None:
            raise Exception('To many connections')

        cg = gevent.getcurrent()
        if hasattr(cg, 'link'):
            cg._db_conn = ret
            cg._db_obj = obj
            cg.link(close_conn)
        return ret

    def pooled__close(obj, conn):
        with _tmp_lock:
            _conn_count[2] += 1

        with db_lock:
            if len(pool) < pool_size:
                conn.rollback()  # if anything left, rollback
                pool.append(conn)
                s.release()
                return
            else:
                s.release()
        with _tmp_lock:
            _conn_count[0] -= 1

        return obj._orig__close(conn)

    l = locals()
    for x in ('_connect', '_close'):
        orig = getattr(orig_db, x)
        setattr(orig_db, "_orig_%s" % x, orig)
        setattr(orig_db, x, l['pooled_%s' % x])

    orig_db._conn_lock = FakeLock()
    return orig_db
