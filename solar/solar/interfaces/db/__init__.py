from solar.interfaces.db.file_system_db import FileSystemDB
from solar.interfaces.db.cached_file_system_db import CachedFileSystemDB

mapping = {
    'cached_file_system': CachedFileSystemDB,
    'file_system': FileSystemDB
}

DB = None

def get_db():
    # Should be retrieved from config
    global DB
    if DB is None:
        DB = mapping['cached_file_system']()
    return DB
