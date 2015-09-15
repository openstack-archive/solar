import json
import requests

from solar.core.log import log
from solar.core import validation


def test(resource):
    log.debug('Testing nova api')

    args = resource.args

    token, token_data = validation.validate_token(
        keystone_host=args['auth_host'],
        keystone_port=args['auth_port'],
        user=args['admin_user'],
        tenant=args['admin_tenant_name'],
        password=args['admin_password'],
    )

    endpoints = [
        e['endpoints'] for e in token_data['access']['serviceCatalog']
        if e['name'] == 'nova'
    ][0]
    public_url = endpoints[0]['publicURL']

    log.debug('nova admin_url: %s', public_url)

    servers = requests.get(
        '{public_url}/servers/detail'.format(public_url=public_url),
        headers={
            'X-Auth-Token': token,
            'Content-Type': 'application/json',
        }
    )

    servers_json = servers.json()

    log.debug(
        'NOVA API SERVERS: %s',
        json.dumps(servers_json, indent=2)
    )

    assert 'servers' in servers_json
    assert isinstance(servers_json['servers'], list)

    flavors = requests.get(
        '{public_url}/flavors'.format(public_url=public_url),
        headers={
            'X-Auth-Token': token,
            'Content-Type': 'application/json',
        }
    )

    flavors_json = flavors.json()

    log.debug('NOVA API FLAVORS: %s', json.dumps(flavors_json, indent=2))

    assert 'flavors' in flavors_json
    assert isinstance(flavors_json['flavors'], list)
    assert len(flavors_json['flavors']) > 0

    for flavor_data in flavors_json['flavors']:
        url = [link['href'] for link in flavor_data['links']
               if link['rel'] == 'self'][0]

        flavor = requests.get(
            url,
            headers={
                'X-Auth-Token': token,
                'Content-Type': 'application/json',
            }
        )

        flavor_json = flavor.json()

        log.debug(
            'NOVA API FLAVOR %s data: %s',
            flavor_data['name'],
            json.dumps(flavor_json, indent=2)
        )

    images = requests.get(
        '{public_url}/images'.format(public_url=public_url),
        headers={
            'X-Auth-Token': token,
            'Content-Type': 'application/json',
        }
    )

    log.debug('NOVA API IMAGES: %s', images.json())
