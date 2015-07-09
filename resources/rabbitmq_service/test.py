import requests

from solar.core.log import log


def test(resource):
    log.debug('Testing rabbitmq_service')

    requests.get('http://%s:%s' % (resource.args['ip'].value, resource.args['management_port'].value))
