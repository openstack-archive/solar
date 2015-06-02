from solar.interfaces.db.file_system_db import FileSystemDB

mapping = {
    'file_system': FileSystemDB
}

DB = None

def get_db():
    # Should be retrieved from config
    global DB
    if DB is None:
        DB = mapping['file_system']()
    return DB
