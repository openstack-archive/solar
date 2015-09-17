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

"""
Validation for meta.yaml files.

Each input looks like this:

ip:
  schema: int!
  value: 5000

or like this:

ip:
  jsonschema:
    type: number
  value: 5000

For more complicated objects:

mount_points:
  schema: [{src: str!, dst: str!}]
  value:

or

mount_points:
  jsonschema:
    type: array
    items:
      type: object
      properties:
        src:
          $ref: #/definitions/object_src
        dst:
          $ref: #/definitions/object_dst
    definitions:
      object_src:
        type: string
        minLength: 1
      object_dst:
        type: string
        minLength: 1
"""

import json
from jsonschema import validate, ValidationError
import requests

from solar.core.log import log




def schema_input_type(schema):
    """Input type from schema

    :param schema:
    :return: simple/list
    """
    if isinstance(schema, list):
        return 'list'

    return 'simple'


def _construct_jsonschema(schema, definition_base=''):
    """Construct jsonschema from our metadata input schema.

    :param schema:
    :return:
    """
    if schema == 'str':
        return {'anyOf': [{'type': 'string'}, {'type': 'null'}]}, {}

    if schema == 'str!':
        return {'type': 'string', 'minLength': 1}, {}

    if schema == 'int':
        return {'anyOf': [{'type': 'number'}, {'type': 'null'}]}, {}
    if schema == 'int!':
        return {'type': 'number'}, {}

    if schema == 'bool':
        return {'anyOf': [{'type': 'boolean'}, {'type': 'null'}]}, {}
    if schema == 'bool!':
        return {'type': 'boolean'}, {}

    print repr(schema)
    print locals()

    if isinstance(schema, list):
        items, definitions = _construct_jsonschema(schema[0], definition_base=definition_base)

        return {
            'type': 'array',
            'items': items,
        }, definitions

    if isinstance(schema, dict):
        properties = {}
        definitions = {}

        for k, v in schema.items():
            if isinstance(v, dict) or isinstance(v, list):
                key = '{}_{}'.format(definition_base, k)
                properties[k] = {'$ref': '#/definitions/{}'.format(key)}
                definitions[key], new_definitions = _construct_jsonschema(v, definition_base=key)
            else:
                properties[k], new_definitions = _construct_jsonschema(v, definition_base=definition_base)

            definitions.update(new_definitions)

        required = [k for k, v in schema.items() if
                    isinstance(v, basestring) and v.endswith('!')]

        ret = {
            'type': 'object',
            'properties': properties,
        }

        if required:
            ret['required'] = required

        return ret, definitions


def construct_jsonschema(schema):
    jsonschema, definitions = _construct_jsonschema(schema)

    jsonschema['definitions'] = definitions

    return jsonschema


def validate_input(value, jsonschema=None, schema=None):
    """Validate single input according to schema.

    :param value: Value to be validated
    :param schema: Dict in jsonschema format
    :param schema: Our custom, simplified schema
    :return: list with errors
    """
    if jsonschema is None:
        jsonschema = construct_jsonschema(schema)
    try:
        validate(value, jsonschema)
    except ValidationError as e:
        return [e.message]
    except Exception as e:
        log.error('jsonschema: %s', jsonschema)
        log.error('value: %s', value)
        log.exception(e)
        raise


def validate_resource(r):
    """Check if resource inputs correspond to schema.

    :param r: Resource instance
    :return: dict, keys are input names, value is array with error.
    """
    ret = {}

    inputs = r.resource_inputs()
    args = r.args

    for input_name, input_definition in inputs.items():
        errors = validate_input(
            args.get(input_name),
            #jsonschema=input_definition.get('jsonschema'),
            schema=input_definition.schema
        )
        if errors:
            ret[input_name] = errors

    return ret


def validate_token(
        keystone_host=None,
        keystone_port=None,
        user=None,
        tenant=None,
        password=None):
    token_data = requests.post(
        'http://%s:%s/v2.0/tokens' % (keystone_host, keystone_port),
        json.dumps({
            'auth': {
                'tenantName': tenant,
                'passwordCredentials': {
                    'username': user,
                    'password': password,
                },
            },
        }),
        headers={'Content-Type': 'application/json'}
    )

    token = token_data.json()['access']['token']['id']

    log.debug('%s TOKEN: %s', user, token)

    return token, token_data.json()
