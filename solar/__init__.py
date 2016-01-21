try:
    from gevent import monkey
except ImportError:
    pass
else:
    monkey.patch_all()
