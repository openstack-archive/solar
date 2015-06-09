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

import os
import collections
from collections import deque
from functools import partial

from solar import utils

from enum import Enum

from solar.interfaces.db import get_db

db = get_db()


STATES = Enum('States', 'error inprogress pending success')


def state_file(name):
    if 'log' in name:
        return Log(name)
    elif 'data' in name:
        return Data(name)


CD = partial(state_file, 'commited_data')
SD = partial(state_file, 'staged_data')
SL = partial(state_file, 'stage_log')
IL = partial(state_file, 'inprogress_log')
CL = partial(state_file, 'commit_log')


class LogItem(object):

    def __init__(self, uid, res_uid, diff, action, state=None):
        self.uid = uid
        self.res = res_uid
        self.diff = diff
        self.state = state or STATES.pending
        self.action = action

    def to_yaml(self):
        return utils.yaml_dump(self.to_dict())

    def to_dict(self):
        return {'uid': self.uid,
                'res': self.res,
                'diff': self.diff,
                'state': self.state.name,
                'action': self.action}

    def __str__(self):
        return self.to_yaml()

    def __repr__(self):
        return self.to_yaml()


class Log(object):

    def __init__(self, path):
        self.path = path
        items = []
        r = db.read(path, collection=db.COLLECTIONS.state_log)
        if r:
            items = r or items

        self.items = deque([LogItem(
            l['uid'], l['res'],
            l['diff'], l['action'],
            getattr(STATES, l['state'])) for l in items])

    def delete(self):
        self.items = deque()
        db.delete(self.path, db.COLLECTIONS.state_log)

    def sync(self):
        db.save(
            self.path,
            [i.to_dict() for i in self.items],
            collection=db.COLLECTIONS.state_log
        )

    def append(self, logitem):
        self.items.append(logitem)
        self.sync()

    def popleft(self):
        item = self.items.popleft()
        self.sync()
        return item

    def pop(self):
        item = self.items.pop()
        self.sync()
        return item

    def show(self, verbose=False):
        return ['L(uuid={0}, res={1}, action={2})'.format(
            l.uid, l.res, l.action) for l in self.items]

    def __repr__(self):
        return 'Log({0})'.format(self.path)

    def __iter__(self):
        return iter(self.items)

    def __nonzero__(self):
        return bool(self.items)


class Data(collections.MutableMapping):

    def __init__(self, path):
        self.path = path
        self.store = {}
        r = db.read(path, collection=db.COLLECTIONS.state_data)
        if r:
            self.store = r or self.store

    def __getitem__(self, key):
        return self.store[key]

    def __setitem__(self, key, value):
        self.store[key] = value
        db.save(self.path, self.store, collection=db.COLLECTIONS.state_data)

    def __delitem__(self, key):
        self.store.pop(key)
        db.save(self.path, self.store, collection=db.COLLECTIONS.state_data)

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)
