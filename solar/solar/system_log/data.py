
import os
import collections
from collections import deque
from functools import partial

from solar import utils
from solar.interfaces.db import get_db

from enum import Enum


db = get_db()


STATES = Enum('States', 'error inprogress pending success')


def state_file(name):
    if 'log' in name:
        return Log(name)
    elif 'data' in name:
        return Data(name)


CD = partial(state_file, 'commited_data')
SL = partial(state_file, 'stage_log')
CL = partial(state_file, 'commit_log')


class LogItem(object):

    def __init__(self, uid, res, diff, action, state=None):
        self.uid = uid
        self.res = res
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

    @classmethod
    def from_dict(cls, **kwargs):
        state = getattr(STATES, kwargs.get('state', ''), STATES.pending)
        kwargs['state'] = state
        return cls(**kwargs)

    def __str__(self):
        return self.to_yaml()

    def __repr__(self):
        return self.to_yaml()


class Log(object):

    def __init__(self, path):
        self.ordered_log = db.get_set(path)

    def append(self, logitem):
        self.ordered_log.add([(logitem.res, logitem.to_dict())])

    def pop(self, uid):
        item = self.get(uid)
        if not item:
            return None
        self.ordered_log.rem([uid])
        return item

    def update(self, logitem):
        self.ordered_log.update(logitem.res, logitem.to_dict())

    def clean(self):
        self.ordered_log.clean()

    def get(self, key):
        item = self.ordered_log.get(key)
        if item:
            return LogItem.from_dict(**item)
        return None

    def collection(self, n=0):
        for item in self.ordered_log.get_left(n):
            yield LogItem.from_dict(**item)

    def __iter__(self):
        return iter(self.collection())


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

    def clean(self):
        db.save(self.path, {}, collection=db.COLLECTIONS.state_data)
