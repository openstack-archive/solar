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


STATES = Enum('States', 'pending inprogress error success')


def state_file(filename):
    filepath = os.path.join(utils.read_config()['state'], filename)
    if 'log' in filename:
        return Log(filepath)
    elif 'data' in filename:
        return Data(filepath)


CD = partial(state_file, 'commited_data')
SD = partial(state_file, 'staged_data')
SL = partial(state_file, 'stage_log')
IL = partial(state_file, 'inprogress_log')
CL = partial(state_file, 'commit_log')


class LogItem(object):

    def __init__(self, uid, res_uid, diff, state=None):
        self.uid = uid
        self.res = res_uid
        self.diff = diff
        self.state = state or STATES.pending

    def to_yaml(self):
        return utils.yaml_dump(self.to_dict())

    def to_dict(self):
        return {'uid': self.uid,
                'res': self.res,
                'diff': self.diff,
                'state': self.state.name}

    def __str__(self):
        return self.to_yaml()

    def __repr__(self):
        return self.to_yaml()


class Log(object):

    def __init__(self, path):
        self.path = path
        items = utils.yaml_load(path) or []
        self.items = deque([LogItem(
            l['uid'], l['res'],
            l['diff'], getattr(STATES, l['state'])) for l in items])

    def sync(self):
        utils.yaml_dump_to([i.to_dict() for i in self.items], self.path)

    def add(self, logitem):
        self.items.append(logitem)
        self.sync()

    def popleft(self):
        item = self.items.popleft()
        self.sync()
        return item

    def show(self, verbose=False):
        return ['L(uuid={0}, res={1})'.format(l.uid, l.res)
                for l in self.items]

    def __repr__(self):
        return 'Log({0})'.format(self.path)

    def __iter__(self):
        return iter(self.items)

    def __nonzero__(self):
        return bool(self.items)


class Data(collections.MutableMapping):

    def __init__(self, path):
        self.path = path
        self.store = utils.yaml_load(path) or {}

    def __getitem__(self, key):
        return self.store[key]

    def __setitem__(self, key, value):
        self.store[key] = value
        utils.yaml_dump_to(self.store, self.path)

    def __delitem__(self, key):
        self.store.pop(key)
        utils.yaml_dump_to(self.store, self.path)

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

