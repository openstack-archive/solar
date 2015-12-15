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

from collections import defaultdict
from .subscription import FuncSub
from .subscription import CollectionSub


class WorkerMeta(type):

    def __new__(cls, name, bases, attrs):

        funcs = []
        for attrname, attrvalue in attrs.iteritems():
            if attrname[0] != '_' and not isinstance(attrvalue, CollectionSub):
                sub = FuncSub(attrvalue)
                attrs[attrname] = sub
                funcs.append(sub)
        return super(WorkerMeta, cls).__new__(cls, name, bases, attrs)


class Worker(object):

    __metaclass__ = WorkerMeta

    for_all = CollectionSub()

    def ping(self, ctxt):
        return 'pong'
