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

import imp
import os
import traceback

from log import log
from solar.core import resource


def test(r):
    if isinstance(r, basestring):
        r = resource.load(r)

    log.debug('Trying {}'.format(r.name))

    script_path = os.path.join(r.db_obj.base_path, 'test.py')
    if not os.path.exists(script_path):
        log.warning('resource {} has no tests'.format(r.name))
        return {}

    log.debug('File {} found'.format(script_path))

    with open(script_path) as f:
        module = imp.load_module(
            '{}_test'.format(r.name),
            f,
            script_path,
            ('', 'r', imp.PY_SOURCE)
        )

    try:
        module.test(r)
        return {
            r.name: {
                'status': 'ok',
            },
        }
    except Exception:
        return {
            r.name: {
                'status': 'error',
                'message': traceback.format_exc(),
            }
        }


def test_all():
    results = {}

    resources = resource.load_all()

    for r in resources:
        ret = test(r)
        if ret:
            results.update(ret)

    return results
