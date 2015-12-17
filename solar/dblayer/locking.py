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

from solar.core.log import log

from solar.dblayer.conflict_resolution import SiblingsError
from solar.dblayer.model import DBLayerNotFound
from solar.dblayer.solar_models import Lock as DBLock


class Lock(object):

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

    @classmethod
    def _acquire(cls, uid, identity):
        try:
            try:
                lk = DBLock.get(uid)
                log.debug(
                    'Found lock with UID %s, owned by %s, owner %r',
                    uid, lk.identity, lk.identity == identity)
            except DBLayerNotFound:
                log.debug(
                    'Create lock UID %s for %s', uid, identity)
                lk = DBLock.from_dict(uid, {'identity': identity})
                lk.save()
        except SiblingsError:
            log.debug(
                'Race condition for lock with UID %s, among %r',
                uid,
                [s.data.get('identity') for s in lk._riak_object.siblings])
            siblings = []
            for s in lk._riak_object.siblings:
                if s.data.get('identity') != identity:
                    siblings.append(s)
            lk._riak_object.siblings = siblings
            lk.save()
        return lk

    @classmethod
    def _release(cls, uid):
        lk = DBLock.get(uid)
        log.debug('Release lock %s with %s', uid, lk.identity)
        lk.delete()

    def __enter__(self):
        lk = self._acquire(self.uid, self.identity)
        if lk.identity != self.identity:
            log.debug(
                'Lock %s acquired by another ideneity %s != %s',
                self.uid, self.identity, lk.identity)
            while self.retries:
                time.sleep(self.wait)
                lk = self._acquire(self.uid, self.identity)
                self.retries -= 1
                if lk.identity == self.identity:
                    break
            else:
                if lk.identity != self.identity:
                    raise RuntimeError(
                        'Failed to acquire {},'
                        ' owned by identity {}'.format(
                            lk.key, lk.identity))
        log.debug('Lock for %s acquired by %s', self.uid, self.identity)

    def __exit__(self, *err):
        self._release(self.uid)
