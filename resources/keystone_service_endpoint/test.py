import jinja2
import json
import requests

from solar.core.log import log


def test(resource):
    log.debug('Testing keystone_service_endpoint %s', resource.name)
    resp = requests.get(
        'http://%s:%s/v3/endpoints' % (resource.args['ip'].value, resource.args['keystone_admin_port'].value),
        headers={
            'X-Auth-Token': resource.args['admin_token'].value,
        }
    )

    resp_json = resp.json()
    assert 'endpoints' in resp_json

    endpoints = {}

    for endpoint in resp_json['endpoints']:
        endpoints[endpoint['interface']] = endpoint['url']

    assert jinja2.Template(resource.args['adminurl'].value).render(**resource.args_dict()) == endpoints['admin']
    assert jinja2.Template(resource.args['internalurl'].value).render(**resource.args_dict()) == endpoints['internal']
    assert jinja2.Template(resource.args['publicurl'].value).render(**resource.args_dict()) == endpoints['public']

    log.debug('%s endpoints: %s', resource.name, json.dumps(resp_json, indent=2))
