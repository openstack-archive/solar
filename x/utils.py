import json
import os
import yaml


def ext_encoder(fpath):
    ext = os.path.splitext(os.path.basename(fpath))[1].strip('.')
    if ext in ['json']:
        return json
    elif ext in ['yaml', 'yml']:
        return yaml

    raise Exception('Unknown extension {}'.format(ext))


def load_file(fpath):
    encoder = ext_encoder(fpath)

    try:
        with open(fpath) as f:
            return encoder.load(f)
    except IOError:
        return {}


def read_config():
    CONFIG_FILE = os.environ.get('CONFIG_FILE') or '/vagrant/config.yaml'
    return load_file(CONFIG_FILE)


def read_config_file(key):
    fpath = read_config()[key]

    return load_file(fpath)


def save_to_config_file(key, data):
    fpath = read_config()[key]

    with open(fpath, 'w') as f:
        encoder = ext_encoder(fpath)
        encoder.dump(data, f)

