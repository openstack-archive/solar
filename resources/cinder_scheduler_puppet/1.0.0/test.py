import requests

from solar.core.log import log


def test(resource):
    log.debug('Testing cinder_scheduler_puppet')
#    requests.get(
#        'http://%s:%s' % (resource.args['ip'], resource.args['port'])
# TODO(bogdando) figure out how to test this
# http://docs.openstack.org/developer/nova/devref/scheduler.html
#    )
