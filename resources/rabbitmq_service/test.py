import requests


def test(resource):
    print 'Testing rabbitmq_service'

    requests.get('http://%s:%s' % (resource.args['ip'].value, resource.args['management_port'].value))
