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

import glob
import io
import json
import logging
import os
import re
import subprocess
import threading
import uuid

from bunch import Bunch
from jinja2 import Environment
import six.moves.urllib.parse as urlparse
import yaml


logger = logging.getLogger(__name__)


def to_json(data):
    return json.dumps(data)


def to_pretty_json(data):
    return json.dumps(data, indent=4)


def communicate(command, data):
    popen = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE)
    return popen.communicate(input=data)[0]


def execute(command, shell=False, env=None):
    popen = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        shell=shell)
    out, err = popen.communicate()
    return popen.returncode, out, err


# Configure jinja2 filters
jinja_env_with_filters = Environment()
jinja_env_with_filters.filters['to_json'] = to_json
jinja_env_with_filters.filters['to_pretty_json'] = to_pretty_json


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
    return str(uuid.uuid4())


def render_template(template_path, **params):
    with io.open(template_path) as f:
        temp = jinja_env_with_filters.from_string(f.read())

    return temp.render(**params)


def ext_encoder(fpath):
    ext = os.path.splitext(os.path.basename(fpath))[1].strip('.')
    if ext in ['json']:
        return json
    elif ext in ['yaml', 'yaml']:
        return yaml

    raise Exception('Unknown extension {}'.format(ext))


def load_file(fpath):
    encoder = ext_encoder(fpath)

    try:
        with open(fpath) as f:
            return encoder.load(f)
    except IOError:
        return {}


def solar_map(funct, args, **kwargs):
    return map(funct, args)


def get_local():
    return threading.local


def parse_database_conn(name):
    regex = re.compile(r'''
            (?P<mode>[\w\+]+)://
            (?:
                (?P<username>[^:/]*)
                (?::(?P<password>[^/]*))?
            @)?
            (?:
                (?P<host>[^/:]*)
                (?::(?P<port>[^/]*))?
            )?
            (?:/(?P<database>.*))?
            ''', re.X)
    if not name:
        raise Exception("Database connection string is empty, "
                        "please ensure that you set config path correctly")
    if '?' in name:
        name, opts = name.split('?', 1)
        opts = dict(urlparse.parse_qsl(opts))
    else:
        opts = {}
    m = regex.match(name)
    if m is not None:
        groups = m.groupdict()
        groups['type'] = 'riak' if groups['mode'] == 'riak' else 'sql'
        return Bunch(groups), Bunch(opts)
    else:
        raise Exception("Invalid database connection string: %r "
                        "It should be in RFC 1738 format. " % name)


def detect_input_schema_by_value(value):
    _types = {
        'int': 'int!',
        'str': 'str!',
        'list': '[]',
        'hash': '{}',
        'list_hash': '[{}]'
    }

    if value is None:
        return ""
    if isinstance(value, int):
        return _types['int']
    if isinstance(value, basestring):
        return _types['str']
    if isinstance(value, list):
        if len(value) >= 1 and isinstance(value[0], dict):
            return _types['list_hash']
        return _types['list']
    if isinstance(value, dict):
        return _types['hash']


def get_current_ident():
    return threading.currentThread().ident
