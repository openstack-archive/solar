import requests

from solar.core.log import log
from solar.core import validation


def test(resource):
    log.debug('Testing glance_puppet')
    requests.get(
        'http://%s:%s' % (resource.args['ip'], resource.args['bind_port'])
    )
    #TODO(bogdando) test packages installed and filesystem store datadir created

    args = resource.args

    token, _ = validation.validate_token(
        keystone_host=args['keystone_host'],
        keystone_port=args['keystone_port'],
        user=args['keystone_user'],
        tenant=args['keystone_tenant'],
        password=args['keystone_password'],
    )
