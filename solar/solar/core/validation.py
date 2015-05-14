from jsonschema import validate, ValidationError


def schema_input_type(schema):
    """Input type from schema

    :param schema:
    :return: simple/list
    """
    if isinstance(schema, list):
        return 'list'

    return 'simple'


def construct_jsonschema(schema):
    """Construct jsonschema from our metadata input schema.

    :param schema:
    :return:
    """

    if schema == 'str':
        return {'type': 'string'}

    if schema == 'str!':
        return {'type': 'string', 'minLength': 1}

    if schema == 'int' or schema == 'int!':
        return {'type': 'number'}

    if isinstance(schema, list):
        return {
            'type': 'array',
            'items': construct_jsonschema(schema[0]),
        }

    if isinstance(schema, dict):
        return {
            'type': 'object',
            'properties': {
                k: construct_jsonschema(v) for k, v in schema.items()
            },
            'required': [k for k, v in schema.items() if
                         isinstance(v, basestring) and v.endswith('!')],
        }


def validate_input(value, jsonschema=None, schema=None):
    """Validate single input according to schema.

    :param value: Value to be validated
    :param schema: Dict in jsonschema format
    :param schema: Our custom, simplified schema
    :return: list with errors
    """
    try:
        if jsonschema:
            validate(value, jsonschema)
        else:
            validate(value, construct_jsonschema(schema))
    except ValidationError as e:
        return [e.message]


def validate_resource(r):
    """Check if resource inputs correspond to schema.

    :param r: Resource instance
    :return: dict, keys are input names, value is array with error.
    """
    ret = {}

    input_schemas = r.metadata['input']
    args = r.args_dict()

    for input_name, input_definition in input_schemas.items():
        errors = validate_input(
            args.get(input_name),
            jsonschema=input_definition.get('jsonschema'),
            schema=input_definition.get('schema')
        )
        if errors:
            ret[input_name] = errors

    return ret
