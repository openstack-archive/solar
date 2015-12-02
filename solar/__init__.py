try:
    from gevent import monkey
except ImportError:
    pass
else:
    monkey.patch_all()
    from solar.dblayer.gevent_patches import patch_all
    patch_all()
