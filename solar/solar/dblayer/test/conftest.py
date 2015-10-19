from riak import RiakClient
from solar.dblayer.model import *
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

Model.get_bucket_name = classmethod(patched_get_bucket_name)

from solar.dblayer.sql import SqlClient
client = SqlClient(':memory:', threadlocals=False, autocommit=False)
# client = SqlClient('blah.db', threadlocals=True,
#                    autocommit=False, pragmas=(('journal_mode', 'WAL'),
#                                               ('synchronous', 'NORMAL')))
# client = RiakClient(protocol='pbc', host='10.0.0.3', pb_port=18087)
# client = RiakClient(protocol='http', host='10.0.0.3', http_port=18098)

ModelMeta.setup(client)
