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

from riak import RiakClient as OrigRiakClient
from riak import RiakError

from solar.dblayer.model import clear_cache


class RiakClient(OrigRiakClient):
    def session_start(self):
        clear_cache()

    def session_end(self, result=True):
        # ignore result
        clear_cache()

    def delete_all(self, cls):
        for _ in xrange(10):
            # riak dislikes deletes without dvv
            try:
                rst = cls.bucket.get_index('$bucket',
                                           startkey='_',
                                           max_results=100000).results
            except RiakError as exc:
                if 'indexes_not_supported' in str(exc):
                    rst = cls.bucket.get_keys()
                else:
                    raise
            for key in rst:
                cls.bucket.delete(key)
            else:
                return
            time.sleep(0.5)
