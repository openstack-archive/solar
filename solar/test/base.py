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
import shutil
import tempfile
import time
import unittest

import yaml

from solar.core.resource import virtual_resource as vr
from solar.dblayer.model import Model


def patched_get_bucket_name(cls):
    return cls.__name__ + str(int(time.time() * 10000))

Model.get_bucket_name = classmethod(patched_get_bucket_name)


class BaseResourceTest(unittest.TestCase):

    def setUp(self):
        self.storage_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.storage_dir)

    def make_resource_meta(self, meta_yaml):
        meta = yaml.load(meta_yaml)
        inps = meta['input']
        # automaticaly add location_id
        inps.setdefault('location_id', {'value': '$uuid',
                                        'reverse': True,
                                        'schema': 'str!'})
        meta_yaml = yaml.dump(meta)

        path = os.path.join(self.storage_dir, meta['id'])
        os.makedirs(path)
        with open(os.path.join(path, 'meta.yaml'), 'w') as f:
            f.write(meta_yaml)

        return path

    def create_resource(self, name, src, args=None):
        args = args or {}
        return vr.create(name, src, args=args)[0]
