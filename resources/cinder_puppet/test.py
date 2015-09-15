import requests

from solar.core.log import log


def test(resource):
    log.debug('Testing cinder_puppet')
    requests.get(
        'http://%s:%s' % (resource.args['ip'], resource.args['port'])
    )
