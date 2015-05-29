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

import collections
from collections import deque


class LogItem(object):

    def __init__(self, uid, res_uid, diff):
        self.uid = uid
        self.res = res_uid
        self.diff = diff

    def to_yaml(self):
        return utils.yaml_dump(self.to_dict())

    def to_dict(self):
        return {'uid': self.uid,
                'res': self.res_uid,
                'diff': self.diff}

    def __str__(self):
        return self.to_yaml()

    def __repr__(self):
        return self.to_yaml()


class Log(object):

    def __init__(self, path):
        self.path = path
        self.items = deque([LogItem(**l) for
                            l in utils.yaml_load(path)])

    def add(self, logitem):
        self.items.append(logitem)
        utils.yaml_dump_to(self.items, path)

    def popleft(self):
        item = self.items.popleft()
        utils.yaml_dump_to(self.items, path)
        return item

    def __repr__(self):
        return 'Log({0})'.format(self.path)


class Data(collections.MutableMapping):

    def __init__(self, path):
        self.path = path
        self.store = utils.yaml_load(path)

    def __getitem__(self, key):
        return self.store[key]

    def __setitem__(self, key, value):
        self.store[key] = value
        utils.yaml_dump_to(self.store, path)

    def __delitem__(self, key):
        self.store.pop(key)
        utils.yaml_dump_to(self.store, path)
