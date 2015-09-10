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

from solar.interfaces.db.redis_db import RedisDB
from solar.interfaces.db.redis_db import FakeRedisDB

mapping = {
    'redis_db': RedisDB,
    'fakeredis_db': FakeRedisDB
}

DB = None


def get_db():
    # Should be retrieved from config
    global DB
    if DB is None:
        DB = mapping['redis_db']()
    return DB
