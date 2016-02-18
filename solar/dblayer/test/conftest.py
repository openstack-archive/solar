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

import pytest
import random
import string


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


def pytest_runtest_setup(item):
    # ALL Computable Inputs tests are in single file
    # so for easy skip we need this
    is_lua = item.name.startswith('test_lua')
    if is_lua:
        try:
            import lupa  # NOQA
        except ImportError:
            pytest.skip("Lupa is required to test lua")


def dicts_to_hashable(list_of_dics):
    rst = []
    for item in list_of_dics:
        rst.append(tuple(item.items()))
    return tuple(rst)


def pytest_namespace():
    return {'dicts_to_hashable': dicts_to_hashable}
