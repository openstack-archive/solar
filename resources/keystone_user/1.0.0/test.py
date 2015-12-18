import requests

from solar.core.log import log
from solar.core import validation


def test(resource):
    log.debug('Testing keystone_user %s', resource.args['user_name'])

    args = resource.args

    token, _ = validation.validate_token(
        keystone_host=args['keystone_host'],
        keystone_port=args['keystone_port'],
        user=args['user_name'],
        tenant=args['tenant_name'],
        password=args['user_password'],
    )
