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

import importlib

db_backends = {
    'neo4j_db': ('solar.interfaces.db.neo4j', 'Neo4jDB'),
    'redis_db': ('solar.interfaces.db.redis_db', 'RedisDB'),
    'fakeredis_db': ('solar.interfaces.db.redis_db', 'FakeRedisDB'),
    'redis_graph_db': ('solar.interfaces.db.redis_graph_db', 'RedisGraphDB'),
    'fakeredis_graph_db': ('solar.interfaces.db.redis_graph_db', 'FakeRedisGraphDB'),
}

CURRENT_DB = 'redis_graph_db'
#CURRENT_DB = 'neo4j_db'

DB = None


def get_db():
    # Should be retrieved from config
    global DB
    if DB is None:
        backend, klass = db_backends[CURRENT_DB]
        module = importlib.import_module(backend)
        DB = getattr(module, klass)()
    return DB
