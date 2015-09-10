import io
import json
import glob
import yaml
import logging
import os

from uuid import uuid4

from jinja2 import Template

logger = logging.getLogger(__name__)


def create_dir(dir_path):
    logger.debug(u'Creating directory %s', dir_path)
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)


def yaml_load(file_path):
    with io.open(file_path) as f:
        result = yaml.load(f)

    return result


def yaml_dump(yaml_data):
    return yaml.safe_dump(yaml_data, default_flow_style=False)


def write_to_file(data, file_path):
    with open(file_path, 'w') as f:
        f.write(data)


def yaml_dump_to(data, file_path):
    write_to_file(yaml_dump(data), file_path)


def find_by_mask(mask):
    for file_path in glob.glob(mask):
        yield os.path.abspath(file_path)


def load_by_mask(mask):
    result = []
    for file_path in find_by_mask(mask):
        result.append(yaml_load(file_path))

    return result


def generate_uuid():
    return str(uuid4())


def render_template(template_path, params):
    with io.open(template_path) as f:
        temp = Template(f.read())

    return temp.render(**params)


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
