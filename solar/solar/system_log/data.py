
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

    def __init__(self, uid, res, log_action, diff, state=None):
        self.uid = uid
        self.res = res
        self.log_action = log_action
        self.diff = diff
        self.state = state or STATES.pending

    def to_yaml(self):
        return utils.yaml_dump(self.to_dict())

    def to_dict(self):
        return {'uid': self.uid,
                'res': self.res,
                'log_action': self.log_action,
                'diff': self.diff,
                'state': self.state.name}

    @classmethod
    def from_dict(cls, **kwargs):
        state = getattr(STATES, kwargs.get('state', ''), STATES.pending)
        kwargs['state'] = state
        return cls(**kwargs)

    def __str__(self):
        return self.compact

    def __repr__(self):
        return self.compact

    @property
    def compact(self):
        return 'log task={} uid={}'.format(self.log_action, self.uid)

    @property
    def details(self):
        return details(self.diff)


def details(diff):
    rst = []
    for type_, val, change in diff:
        if type_ == 'add':
            for key, val in change:
                rst.append('++ {}: {}'.format(key ,val))
        elif type_ == 'change':
            rst.append('-+ {}: {} >> {}'.format(
                unwrap_change_val(val), change[0], change[1]))
    return rst


def unwrap_add(it):
    if isinstance(it, dict):
        if it['emitter']:
            return '{}::{}'.format(it['emitter'], it['value'])
        return it['value']
    elif isinstance(it, list):
        return [unwrap_add(i) for i in it]
    else:
        return it[1]


def unwrap_change_val(val):
    if isinstance(val, list):
        return '{}:[{}] '.format(val[0], val[1])
    else:
        return val


class Log(object):

    def __init__(self, path):
        self.ordered_log = db.get_ordered_hash(path)

    def append(self, logitem):
        self.ordered_log.add([(logitem.log_action, logitem.to_dict())])

    def pop(self, uid):
        item = self.get(uid)
        if not item:
            return None
        self.ordered_log.rem([uid])
        return item

    def update(self, logitem):
        self.ordered_log.update(logitem.log_action, logitem.to_dict())

    def clean(self):
        self.ordered_log.clean()

    def get(self, key):
        item = self.ordered_log.get(key)
        if item:
            return LogItem.from_dict(**item)
        return None

    def collection(self, n=0):
        for item in self.ordered_log.reverse(n=n):
            yield LogItem.from_dict(**item)

    def reverse(self, n=0):
        for item in self.ordered_log.list(n=n):
            yield LogItem.from_dict(**item)

    def __iter__(self):
        return iter(self.collection())


class Data(collections.MutableMapping):

    def __init__(self, path):
        self.path = path
        self.store = {}
        r = db.get(path, collection=db.COLLECTIONS.state_data,
                   return_empty=True, db_convert=False)
        if r:
            self.store = r or self.store

    def __getitem__(self, key):
        return self.store[key]

    def __setitem__(self, key, value):
        self.store[key] = value
        db.create(self.path, self.store, collection=db.COLLECTIONS.state_data)

    def __delitem__(self, key):
        self.store.pop(key)
        db.create(self.path, self.store, collection=db.COLLECTIONS.state_data)

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def clean(self):
        db.create(self.path, {}, collection=db.COLLECTIONS.state_data)
