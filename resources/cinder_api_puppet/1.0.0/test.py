import requests

from solar.core.log import log


def test(resource):
    log.debug('Testing cinder_api_puppet')
    requests.get(
        'http://%s:%s' % (resource.args['ip'], resource.args['service_port'])
    )
