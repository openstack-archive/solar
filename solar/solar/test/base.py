import os
import shutil
import tempfile
import unittest
import yaml

from solar.core import resource as xr
from solar.core import signals as xs
from solar.interfaces.db import get_db

db = get_db()


class BaseResourceTest(unittest.TestCase):
    def setUp(self):
        self.storage_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.storage_dir)
        db.clear()
        xs.Connections.clear()

    def make_resource_meta(self, meta_yaml):
        meta = yaml.load(meta_yaml)

        path = os.path.join(self.storage_dir, meta['id'])
        os.makedirs(path)
        with open(os.path.join(path, 'meta.yaml'), 'w') as f:
            f.write(meta_yaml)

        return path

    def create_resource(self, name, src, args):
        return xr.create(name, src, args)
