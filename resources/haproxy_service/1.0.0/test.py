import requests

from solar.core.log import log


def test(resource):
    log.debug('Testing haproxy_service')
    requests.get(
        'http://%s:%s' % (resource.args['ip'], resource.args['ports'][0][0])
    )
