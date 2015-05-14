from solar.interfaces.db.file_system_db import FileSystemDB

mapping = {
    'file_system': FileSystemDB
}

def get_db():
    # Should be retrieved from config
    return mapping['file_system']()
