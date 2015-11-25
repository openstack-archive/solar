"""
Starts single seession, and ends it with `atexit`
can be used from cli / examples
shouldn't be used from long running processes (workers etc)

"""

try:
    from gevent import monkey
except ImportError:
    pass
else:
    monkey.patch_all()
    from solar.dblayer.gevent_patches import patch_all
    patch_all()


def create_all():

    import sys
    if sys.executable.startswith(('python', )):
        # auto add session to only standalone python runs
        return

    from solar.dblayer.model import ModelMeta

    import atexit

    ModelMeta.session_start()

    atexit.register(ModelMeta.session_end)
