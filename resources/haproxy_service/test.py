import requests

from solar.core.log import log


def test(resource):
    log.debug('Testing haproxy_service')
    requests.get(
        'http://%s:%s' % (resource.args['ip'].value, resource.args['ports'].value[0]['value'][0]['value'])
    )
