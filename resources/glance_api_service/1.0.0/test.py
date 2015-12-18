import requests

from solar.core.log import log
from solar.core import validation


def test(resource):
    log.debug('Testing glance_service')

    args = resource.args

    token, _ = validation.validate_token(
        keystone_host=args['keystone_host'],
        keystone_port=args['keystone_port'],
        user='glance_admin',
        tenant='services',
        password=args['keystone_password'],
    )

    images = requests.get(
        'http://%s:%s/v1/images' % (resource.args['ip'], 9393),
        headers={'X-Auth-Token': token}
    )
    assert images.json() == {'images': []}
