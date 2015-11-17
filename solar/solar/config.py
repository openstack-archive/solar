import os
import yaml
from bunch import Bunch

CWD = os.getcwd()

C = Bunch()
C.redis = Bunch(port='6379', host='10.0.0.2')
C.riak = Bunch(port='8087', host='10.0.0.2', protocol='pbc')
C.sqlite = Bunch(backend='memory', location=':memory:')
C.dblayer = 'riak'


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
        os.path.join(CWD, '.config.override')
        ]
    data = {}

    def _load_from_path(data, path):
        with open(path) as f:
            loaded = yaml.load(f)
            if loaded:
                data.update(loaded)

    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path) as f:
            loaded = yaml.load(f)
            if loaded:
                data.update(loaded)

    def _setter(config, path):
        vals = data
        for key in path:
            vals = vals[key]
        config[path[-1]] = vals
    _lookup_vals(_setter, C)

def from_env():
    def _setter(config, path):
        env_key = '_'.join(path).upper()
        if env_key in os.environ:
            config[path[-1]] = os.environ[env_key]
    _lookup_vals(_setter, C)

from_configs()
from_env()
