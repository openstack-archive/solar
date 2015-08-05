import requests

from solar.core.log import log
from solar.core import validation


def test(resource):
    log.debug('Testing glance_puppet')
    requests.get(
        'http://%s:%s' % (resource.args['ip'].value, resource.args['bind_port'].value)
    )
    #TODO(bogdando) test packages installed and filesystem store datadir created

    args = resource.args

    token, _ = validation.validate_token(
        keystone_host=args['keystone_host'].value,
        keystone_port=args['keystone_port'].value,
        user=args['keystone_user'].value,
        tenant=args['keystone_tenant'].value,
        password=args['keystone_password'].value,
    )
