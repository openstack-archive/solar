from solar.dblayer.model import ModelMeta

import atexit

ModelMeta.session_start()

atexit.register(ModelMeta.session_end)
