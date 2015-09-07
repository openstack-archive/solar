
from solar.interfaces.db.neo4j import Neo4jDB
from solar.interfaces.db.redis_db import RedisDB
from solar.interfaces.db.redis_db import FakeRedisDB
from solar.interfaces.db.redis_graph_db import RedisGraphDB
from solar.interfaces.db.redis_graph_db import FakeRedisGraphDB

mapping = {
    'neo4j_db': Neo4jDB,
    'fakeredis_db': FakeRedisDB,
    'redis_db': RedisDB,
    'fakeredis_graph_db': FakeRedisGraphDB,
    'redis_graph_db': RedisGraphDB,
}

CURRENT_DB = 'redis_graph_db'
CURRENT_DB = 'neo4j_db'

DB = None


def get_db():
    # Should be retrieved from config
    global DB
    if DB is None:
        DB = mapping[CURRENT_DB]()
    return DB
