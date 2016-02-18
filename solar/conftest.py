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

import os
import pytest
import time

from solar.config import C
C.solar_db = C.solar_db.format(PID=os.getpid())

from solar.dblayer.model import get_bucket
from solar.dblayer.model import Model
from solar.dblayer.model import ModelMeta
from solar import utils


# workaround to provide test result in other fixtures
# https://github.com/pytest-dev/pytest/issues/288
@pytest.fixture
def solar_testresult():
    class TestResult(object):
        rep = None

    return TestResult()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    result = yield
    rep = result.get_result()
    if 'solar_testresult' in item.fixturenames:
        if 'solar_testresult' not in item.funcargs:
            return
        item.funcargs['solar_testresult'].rep = rep
# end of workaround


def pytest_addoption(parser):
    parser.addoption(
        "--clean", action="store_true", default=False,
        help="Use this option for additional cleanup")


def pytest_unconfigure(config):
    if config.getoption("clean"):
        db, opts = utils.parse_database_conn(C.solar_db)
        if db.mode == 'sqlite' and os.path.isfile(db.database):
            os.unlink(db.database)


def patched_get_bucket_name(cls):
    return cls.__name__ + str(os.getpid()) + str(time.time())


Model.get_bucket_name = classmethod(patched_get_bucket_name)


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


@pytest.fixture(autouse=True)
def setup(request, solar_testresult):

    for model in ModelMeta._defined_models:
        model.bucket = get_bucket(None, model, ModelMeta)

    _connection, _ = utils.parse_database_conn(C.solar_db)
    if _connection.type == 'sql':

        def drop_tables_on_sql():
            # clean only when tests crashed
            if solar_testresult.rep.failed:
                return
            for model in ModelMeta._defined_models:
                model.bucket._sql_idx.drop_table(fail_silently=False)
                model.bucket._sql_model.drop_table(fail_silently=False)

        request.addfinalizer(drop_tables_on_sql)
