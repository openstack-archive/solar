from solar.interfaces.db.file_system_db import FileSystemDB
from solar.interfaces.db.cached_file_system_db import CachedFileSystemDB

mapping = {
    'cached_file_system': CachedFileSystemDB,
    'file_system': FileSystemDB
}

def get_db():
    # Should be retrieved from config
    #return mapping['file_system']()
    return mapping['cached_file_system']()
