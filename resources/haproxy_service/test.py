import requests


def test(resource):
    print 'Testing haproxy_service'
    requests.get(
        'http://%s:%s' % (resource.args['ip'].value, resource.args['ports'].value[0]['value'][0]['value'])
    )
