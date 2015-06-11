from solar.interfaces.db.cached_file_system_db import CachedFileSystemDB
from solar.interfaces.db.file_system_db import FileSystemDB
from solar.interfaces.db.redis_db import RedisDB

mapping = {
    'cached_file_system': CachedFileSystemDB,
    'file_system': FileSystemDB,
    'redis_db': RedisDB,
}

DB = None


def get_db():
    # Should be retrieved from config
    global DB
    if DB is None:
        DB = mapping['redis_db']()
    return DB
