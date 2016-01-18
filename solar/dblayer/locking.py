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
from solar.dblayer.solar_models import Lock as DBLock

from uuid import uuid4


class _Lock(object):

    def __init__(self, uid, identity, retries=0, wait=1):
        """Storage based lock mechanism

        :param uid: target of lock
        :param identity: unit of concurrency
        :param retries: retries of acquiring lock
        :param wait: sleep between retries
        """

        self.uid = uid
        self.identity = identity
        self.retries = retries
        self.wait = wait
        self.stamp = str(uuid4())

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
                'Lock %s acquired by another identity %s != %s',
                self.uid, self.identity, lk.who_is_locking())
            while self.retries:
                del DBLock._c.obj_cache[lk.key]
                time.sleep(self.wait)
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
        log.debug('Lock for %s acquired by %s', self.uid, self.identity)

    def __exit__(self, *err):
        self._release(self.uid, self.identity, self.stamp)


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
        try:
            lk = DBLock.get(uid)
        except DBLayerNotFound:
            log.debug(
                'Create lock UID %s for %s', uid, identity)
            lk = DBLock.from_dict(uid, {})
            lk.change_locking_state(identity, 1, stamp)
            lk.save(force=True)
        else:
            locking = lk.who_is_locking()
            if locking is not None:
                log.debug(
                    'Found lock with UID %s, owned by %s, owner %r',
                    uid, locking, lk.am_i_locking(identity))
                return lk
            else:
                log.debug(
                    'Create lock UID %s for %s', uid, identity)
                lk.change_locking_state(identity, 1, stamp)
                lk.save(force=True)
        del DBLock._c.obj_cache[lk.key]
        lk = DBLock.get(uid)
        locking = lk.who_is_locking()
        if locking is not None and identity != locking:
            if [identity, 1, stamp] in lk.lockers:
                lk.change_locking_state(identity, -1, stamp)
                lk.save(force=True)
                log.debug("I was not locking, so removing me %s" % identity)
        return lk


class RiakLock(_CRDTishLock):
    pass


class SQLiteLock(_CRDTishLock):
    pass


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
            # TODO object shouldnt be cached before successfull save
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
