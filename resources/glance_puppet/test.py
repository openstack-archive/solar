import requests

from solar.core.log import log


def test(resource):
    log.debug('Testing glance_puppet')
    requests.get(
        'http://%s:%s' % (resource.args['ip'].value, resource.args['port'].value)
    )
    #TODO(bogdando) test packages installed and filesystem store datadir created
