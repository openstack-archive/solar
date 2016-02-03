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

from oslo_config import cfg


class SolarConf(cfg.ConfigOpts):
    """oslo_config performs default config files search based on
    provided project name
    """

    @staticmethod
    def _make_config_options(defaultconfigfiles):
        config = os.environ.get('SOLAR_CONFIG', None)
        config_files = defaultconfigfiles[:]
        if config:
            config_files.append(config)
        return cfg.ConfigOpts._make_config_options(config_files)

    def __call__(self, *args, **kwargs):
        if 'project' not in kwargs:
            kwargs['project'] = 'solar'
        return super(SolarConf, self).__call__(*args, **kwargs)


C = SolarConf()

C.register_opts([
    cfg.StrOpt(
        'solar_db',
        default=os.environ.get('SOLAR_DB', 'sqlite:////tmp/solar.db')),
    cfg.BoolOpt('riak_ensemble', default=False),
    cfg.StrOpt('lock_bucket_type'),
    cfg.StrOpt('counter_bucket_type'),
    cfg.StrOpt('log_file', default='solar.log'),
    cfg.StrOpt('system_log_address',
               default='ipc:///tmp/solar_system_log'),
    cfg.StrOpt('tasks_address',
               default='ipc:///tmp/solar_tasks'),
    cfg.StrOpt('scheduler_address',
               default='ipc:///tmp/solar_scheduler'),
    cfg.StrOpt('executor', default='zerorpc'),
    cfg.StrOpt('tasks_driver', default='solar'),
    cfg.StrOpt('scheduler_driver', default='solar'),
    cfg.StrOpt('system_log_driver', default='solar'),
    cfg.StrOpt('runner', default='gevent')])

if not os.environ.get('DISABLE_CONFIG_FILES', False):
    C([])
