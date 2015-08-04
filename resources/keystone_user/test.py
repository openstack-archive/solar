import requests

from solar.core.log import log
from solar.core import validation


def test(resource):
    log.debug('Testing keystone_user %s', resource.args['user_name'].value)

    args = resource.args

    token, _ = validation.validate_token(
        keystone_host=args['keystone_host'].value,
        keystone_port=args['keystone_port'].value,
        user=args['user_name'].value,
        tenant=args['tenant_name'].value,
        password=args['user_password'].value,
    )
