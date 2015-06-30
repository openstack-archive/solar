import json
import requests


def test(resource):
    print 'Testing glance_service'
    token_data = requests.post(
        'http://%s:%s/v2.0/tokens' % (resource.args['ip'].value, resource.args['listen_port'].value),
        json.dumps({
            'auth': {
                'tenantName': resource.args['tenant_name'].value,
                'passwordCredentials': {
                    'username': resource.args['user_name'].value,
                    'password': resource.args['user_password'].value,
                    }
            }
        }),
        headers={'Content-Type': 'application/json'}
    )

    token = token_data.json()['access']['token']['id']
    print 'GLANCE TOKEN: {}'.format(token)

    images = requests.get(
        'http://%s:%s/v1/images' % (resource.args['ip'].value, resource.args['listen_port'].value),
        headers={'X-Auth-Token': token}
    )
    assert images.json() == {'images': []}
