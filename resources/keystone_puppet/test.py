import requests


def test(resource):
    print 'Testing keystone_puppet'
    requests.get(
        'http://%s:%s' % (resource.args['ip'].value, resource.args['port'].value)
    )
