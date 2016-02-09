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

import time

from solar.config import C
from solar.utils import parse_database_conn

_connection, _connection_details = parse_database_conn(C.solar_db)

if _connection.mode == 'riak':
    from riak import RiakError

from solar.core.log import log
from solar.dblayer.model import DBLayerNotFound
from solar.dblayer.model import ModelMeta
from solar.dblayer.solar_models import Lock as DBLock

from threading import Semaphore

from uuid import uuid4


class LockWaiter(object):

    def __init__(self):
        pass

    def wait(self, uid, identity):
        raise NotImplementedError()

    def notify(self, uid, identity, state):
        raise NotImplementedError()


class NaiveWaiter(LockWaiter):
    """Works like time.sleep(timeout)"""

    def __init__(self, timeout):
        self.timeout = timeout

    def wait(self, uid, identity):
        time.sleep(self.timeout)
        return True

    def notify(self, uid, identity, state):
        return True


class SemaWaiter(LockWaiter):
    """Simple wait improvement that waits on semaphore
It waits on non blocking semaphore in a loop.
Other thread *may* release semaphore, then wait loop finishes.
If nothing released semaphore, it works like time.sleep(timeout)
"""

    _sema = Semaphore()
    _last = (None, None, -1)

    def __init__(self, timeout):
        self.timeout = timeout
        self._delay = 0.02

    def wait(self, uid, identity):
        tries = self.timeout / self._delay
        while tries:
            result = self._sema.acquire(blocking=False)
            if result:
                return True
            else:
                time.sleep(self._delay)
        return False

    def notify(self, uid, identity, state):
        if state == 0:
            self._sema.release()
        return True


class _Lock(object):

    def __init__(self, uid, identity, retries=0, waiter=None):
        """Storage based lock mechanism

        :param uid: target of lock
        :param identity: unit of concurrency
        :param retries: retries of acquiring lock
        :param wait: sleep between retries
        """

        self.uid = uid
        self.identity = identity
        self.retries = retries
        if waiter is None:
            waiter = Waiter(1)
        self.waiter = waiter
        self.stamp = str(uuid4())

    @classmethod
    def _after_acquire(cls, uid, identity):
        """Will be called after lock successfully acquired."""

    @classmethod
    def _before_retry(cls, uid, identity):
        """WIll be called before retry."""

    @classmethod
    def _acquire(cls, uid, identity):
        raise NotImplemented(
            'Different strategies for handling collisions')

    @classmethod
    def _release(cls, uid, identity):
        lk = DBLock.get(uid)
        log.debug('Release lock %s with %s', uid, identity)
        lk.delete()

    def __enter__(self):
        lk = self._acquire(self.uid, self.identity, self.stamp)
        if not lk.am_i_locking(self.identity):
            log.debug(
                'Lock %s acquired by another identity %s != %s, lockers %s',
                self.uid, self.identity, lk.who_is_locking(), lk.lockers)
            while self.retries:
                self._before_retry(self.uid, self.identity)
                if lk.key in DBLock._c.obj_cache:
                    del DBLock._c.obj_cache[lk.key]
                self.waiter.wait(self.uid, self.identity)
                lk = self._acquire(self.uid, self.identity, self.stamp)
                self.retries -= 1
                if lk.am_i_locking(self.identity):
                    break
                else:
                    # reset stamp mark
                    self.stamp = str(uuid4())
            else:
                if not lk.am_i_locking(self.identity):
                    raise RuntimeError(
                        'Failed to acquire {},'
                        ' owned by identity {}'.format(
                            lk.key, lk.who_is_locking()))
        self._after_acquire(self.uid, self.identity)
        log.debug('Lock for %s acquired by %s', self.uid, self.identity)
        return lk

    def __exit__(self, *err):
        self._release(self.uid, self.identity, self.stamp)
        self.waiter.notify(self.uid, self.identity, 0)


class _CRDTishLock(_Lock):

    @classmethod
    def _release(cls, uid, identity, stamp):
        log.debug("Release lock %s with %s", uid, identity)
        lk = DBLock.get(uid)
        lk.change_locking_state(identity, -1, stamp)
        lk.save(force=True)

    @classmethod
    def _acquire(cls, uid, identity, stamp):
        try:
            del DBLock._c.obj_cache[uid]
        except KeyError:
            pass
        _check = True
        try:
            lk = DBLock.get(uid)
        except DBLayerNotFound:
            log.debug(
                'Create new lock UID %s for %s', uid, identity)
            lk = DBLock.from_dict(uid, {})
            lk.change_locking_state(identity, 1, stamp)
            lk.save(force=True)
            if len(lk.sum_all().keys()) != 1:
                # concurrent create
                lk.change_locking_state(identity, -1, stamp)
                lk.save(force=True)
                log.debug("Concurrent lock %s create", uid)
            else:
                _check = False
        if _check:
            locking = lk.who_is_locking()
            if locking is not None:
                log.debug(
                    'Found lock with UID %s, owned by %s,'
                    ' owner %r, lockers %s',
                    uid, locking, lk.am_i_locking(identity), lk.lockers)
                return lk
            else:
                log.debug(
                    'Create lock UID %s for %s', uid, identity)
                lk.change_locking_state(identity, 1, stamp)
                lk.save(force=True)
        summed = lk.sum_all()
        if len(summed.keys()) != 1:
            log.debug("More than one acquire")
            if identity in summed:
                lk.change_locking_state(identity, -1, stamp)
                lk.save(force=True)
                log.debug("I may be not locking, so removing me %s", identity)
        return lk


class RiakLock(_CRDTishLock):
    pass


class SQLiteLock(_CRDTishLock):

    @classmethod
    def _end_start_session(cls, uid, identity):
        """Because of isolated versions of data in concurrent sessions
        we need to ensure that session will be re-started at certain
        hooks during locking logic
        """
        ModelMeta.session_end()
        ModelMeta.session_start()

    _after_acquire = _end_start_session
    _before_retry = _end_start_session


class RiakEnsembleLock(_Lock):

    @classmethod
    def _acquire(cls, uid, identity, stamp):
        try:
            log.debug(
                'Create lock UID %s for %s', uid, identity)
            lk = DBLock.from_dict(uid, {'identity': identity})
            lk.save(force=True)
            return lk
        except RiakError as exc:
            # TODO object shouldnt be cached before successful save
            del DBLock._c.obj_cache[lk.key]
            # check documentation for error message
            # http://docs.basho.com/riak/latest/dev/advanced/strong-consistency/#Error-Messages
            if 'failed' in str(exc):
                lk = DBLock.get(uid)
                log.debug('Lock %s already acquired by %s', uid, lk.identity)
                return lk
            raise


if _connection.mode == 'sqlite':
    Lock = SQLiteLock
elif _connection.mode == 'riak':
    if C.riak_ensemble:
        Lock = RiakEnsembleLock
    else:
        Lock = RiakLock

# Waiter = NaiveWaiter
Waiter = SemaWaiter
