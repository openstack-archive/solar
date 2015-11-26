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
from gevent.pool import Pool


class DBLayerPool(Pool):
    def __init__(self, *args, **kwargs):
        super(DBLayerPool, self).__init__(*args, **kwargs)
        self.parent = gevent.getcurrent()

    def spawn(self, *args, **kwargs):
        greenlet = self.greenlet_class(*args, **kwargs)
        greenlet._nested_parent = self.parent
        self.start(greenlet)
        return greenlet


@classmethod
def multi_get(obj, keys):
    pool = DBLayerPool(5)
    return pool.map(obj.get, keys)


def solar_map(funct, args, concurrency=5):
    dp = DBLayerPool(concurrency)
    return dp.map(funct, args)


def get_local():
    from solar.dblayer.gevent_local import local
    return local
