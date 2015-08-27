
from solar.interfaces.db.neo4j import Neo4jDB
from solar.interfaces.db.redis_db import RedisDB
from solar.interfaces.db.redis_db import FakeRedisDB

mapping = {
    'neo4j_db': Neo4jDB,
    'redis_db': RedisDB,
    'fakeredis_db': FakeRedisDB
}

DB = None


def get_db():
    # Should be retrieved from config
    global DB
    if DB is None:
        DB = mapping['neo4j_db']()
    return DB
