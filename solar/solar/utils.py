import io
import glob
import yaml
import logging
import os

logger = logging.getLogger(__name__)


def create_dir(dir_path):
    logger.debug(u'Creating directory %s', dir_path)
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)


def load_yaml(file_path):
    with io.open(file_path) as f:
        result = yaml.load(f)

    return result


def yaml_dump(yaml_data):
    return yaml.dump(yaml_data, default_flow_style=False)


def load_by_mask(mask):
    result = []
    for file_path in glob.glob(mask):
        result.extend(load_yaml(file_path))

    return result
