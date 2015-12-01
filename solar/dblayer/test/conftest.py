#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import random
import string
import time

import pytest


from solar.dblayer.model import get_bucket
from solar.dblayer.model import Model
from solar.dblayer.model import ModelMeta


def patched_get_bucket_name(cls):
    return cls.__name__ + str(time.time())


class RndObj(object):
    def __init__(self, name):
        self.rnd = name + ''.join((random.choice(string.ascii_lowercase)
                                   for x in xrange(8)))
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


def dicts_to_hashable(list_of_dics):
    rst = []
    for item in list_of_dics:
        rst.append(tuple(item.items()))
    return tuple(rst)


def pytest_namespace():
    return {'dicts_to_hashable': dicts_to_hashable}


Model.get_bucket_name = classmethod(patched_get_bucket_name)
