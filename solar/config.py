#
# Copyright 2015 Mirantis, Inc.
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
#

import os

from bunch import Bunch
import yaml


CWD = os.getcwd()


C = Bunch(solar_db="")
C.celery_broker = 'sqla+sqlite:////tmp/celery.db'
C.celery_backend = 'db+sqlite:////tmp/celery.db'
C.riak_ensemble = False
C.lock_bucket_type = None
C.counter_bucket_type = None
C.log_file = 'solar.log'
C.system_log_address = 'ipc:///tmp/solar_system_log'
C.tasks_address = 'ipc:///tmp/solar_tasks'
C.scheduler_address = 'ipc:///tmp/solar_scheduler'


def _lookup_vals(setter, config, prefix=None):
    for key, val in config.iteritems():
        if prefix is None:
            sub = [key]
        else:
            sub = prefix + [key]
        if isinstance(val, Bunch):
            _lookup_vals(setter, val, sub)
        else:
            setter(config, sub)


def from_configs():

    paths = [
        os.getenv('SOLAR_CONFIG', os.path.join(CWD, '.config')),
        os.getenv('SOLAR_CONFIG_OVERRIDE', None),
        os.path.join(CWD, '.config.override')
    ]
    data = {}

    def _load_from_path(data, path):
        with open(path) as f:
            loaded = yaml.load(f)
            if loaded:
                data.update(loaded)

    for path in paths:
        if not path:
            continue
        if not os.path.exists(path):
            continue
        if not os.path.isfile(path):
            continue
        with open(path) as f:
            loaded = yaml.load(f)
            if loaded:
                data.update(loaded)

    def _setter(config, path):
        vals = data
        for key in path:
            if key not in vals:
                return
            vals = vals[key]
        config[path[-1]] = vals
    if data:
        _lookup_vals(_setter, C)


def from_env():
    def _setter(config, path):
        env_key = '_'.join(path).upper()
        if env_key in os.environ:
            config[path[-1]] = os.environ[env_key]
    _lookup_vals(_setter, C)

from_configs()
from_env()
