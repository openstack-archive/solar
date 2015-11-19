from solar.dblayer.model import Model, ModelMeta, get_bucket
import pytest
import time
import string
import random

def patched_get_bucket_name(cls):
    return cls.__name__ + str(time.time())

class RndObj(object):

    def __init__(self, name):
        self.rnd = name + ''.join((random.choice(string.ascii_lowercase) for x in xrange(8)))
        self.calls = 0

    def next(self):
        num = self.calls
        self.calls += 1
        return (self.rnd + str(num))

    def __iter__(self):
        return self

@pytest.fixture(scope='function')
def rk(request):

    name = request.module.__name__ + request.function.__name__

    obj = RndObj(name)

    return obj

@pytest.fixture(scope='function')
def rt(request):

    name = request.module.__name__ + request.function.__name__

    obj = RndObj(name)

    return obj


@pytest.fixture(autouse=True)
def setup(request):

    for model in ModelMeta._defined_models:
        model.bucket = get_bucket(None, model, ModelMeta)


def pytest_runtest_teardown(item, nextitem):
    ModelMeta.session_end(result=True)
    return nextitem

def pytest_runtest_call(item):
    ModelMeta.session_start()


Model.get_bucket_name = classmethod(patched_get_bucket_name)
