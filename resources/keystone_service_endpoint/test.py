import jinja2
import json
import requests

from solar.core.log import log


def test(resource):
    log.debug('Testing keystone_service_endpoint %s', resource.name)

    resp = requests.get(
        'http://%s:%s/v3/services' % (resource.args['ip'].value, resource.args['keystone_admin_port'].value),
        headers={
            'X-Auth-Token': resource.args['admin_token'].value,
            }
    )

    resp_json = resp.json()
    assert 'services' in resp_json

    service = [s for s in resp_json['services'] if s['name'] == resource.args['endpoint_name'].value][0]
    service_id = service['id']

    assert service['description'] == resource.args['description'].value

    log.debug('%s service: %s', resource.name, json.dumps(service, indent=2))

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
        if endpoint['service_id'] == service_id:
            endpoints[endpoint['interface']] = endpoint

    assert jinja2.Template(resource.args['adminurl'].value).render(**resource.args_dict()) == endpoints['admin']['url']
    assert jinja2.Template(resource.args['internalurl'].value).render(**resource.args_dict()) == endpoints['internal']['url']
    assert jinja2.Template(resource.args['publicurl'].value).render(**resource.args_dict()) == endpoints['public']['url']

    log.debug('%s endpoints: %s', resource.name, json.dumps(endpoints, indent=2))

