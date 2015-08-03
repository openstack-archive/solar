import requests

from solar.core.log import log


def test(resource):
    log.debug('Testing glance_registry_puppet')
    requests.get(
        'http://%s:%s' % (resource.args['ip'].value, resource.args['bind_port'].value)
    )
