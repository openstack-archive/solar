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
from solar.dblayer.model import Model, ModelMeta, get_bucket
import pytest
import time


def patched_get_bucket_name(cls):
    return cls.__name__ + str(time.time())

@pytest.fixture(autouse=True)
def setup(request):

    for model in ModelMeta._defined_models:
        model.bucket = get_bucket(None, model, ModelMeta)


@pytest.fixture(autouse=True)
def setup(request):

    for model in ModelMeta._defined_models:
        model.bucket = get_bucket(None, model, ModelMeta)

def pytest_runtest_teardown(item, nextitem):
    ModelMeta.session_end(result=True)
    return nextitem

# It will run before all fixtures
def pytest_runtest_setup(item):
    ModelMeta.session_start()

# it will run after fixtures but before test
def pytest_runtest_call(item):
    ModelMeta.session_end()
    ModelMeta.session_start()


Model.get_bucket_name = classmethod(patched_get_bucket_name)
