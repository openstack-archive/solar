import requests

from solar.core.log import log


def test(resource):
    log.debug('Testing cinder_volume_puppet')
#    requests.get(
#        'http://%s:%s' % (resource.args['ip'].value, resource.args['port'].value)
# TODO(bogdando) figure out how to test this
# http://docs.openstack.org/developer/nova/devref/volume.html
    )
