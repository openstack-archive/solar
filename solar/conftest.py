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
import sys

from solar.config import C
from solar import utils

conf_args = []
delimiter = '--'
if delimiter in sys.argv:
    conf_args = sys.argv[sys.argv.index(delimiter) + 1:]
C(conf_args)
C.solar_db = C.solar_db.format(PID=os.getpid())


def pytest_addoption(parser):
    parser.addoption(
        "--clean", action="store_true", default=False,
        help="Use this option for additional cleanup")


def pytest_unconfigure(config):
    if config.getoption("clean"):
        db, opts = utils.parse_database_conn(C.solar_db)
        if db.mode == 'sqlite' and os.path.isfile(db.database):
            os.unlink(db.database)
