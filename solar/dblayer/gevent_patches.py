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


def _patch(obj, name, target):
    orig = getattr(obj, name)
    setattr(obj, '_orig_%s' % name, orig)
    setattr(obj, name, target)


def patch_all():
    from solar.config import C
    from solar.dblayer.model import ModelMeta
    if ModelMeta._defined_models:
        raise RuntimeError(
            "You should run patch_multi_get before defining models")

    from solar.dblayer.model import Model

    from solar.dblayer.gevent_helpers import get_local
    from solar.dblayer.gevent_helpers import multi_get
    from solar.dblayer.gevent_helpers import solar_map
    from solar import utils

    if C.solar_db.startswith('riak'):
        # patching these methods on sql
        # dbs does not make sense
        _patch(Model, 'multi_get', multi_get)
        _patch(utils, 'solar_map', solar_map)

    _patch(utils, 'get_local', get_local)
    _patch(Model, '_local', get_local()())
