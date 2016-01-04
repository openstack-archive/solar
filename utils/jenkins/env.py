# -*- coding: utf-8 -*-
import os
import yaml

from devops.models import Environment


def create_config():
    env = os.environ

    conf_path = env['CONF_PATH']
    with open(conf_path) as c:
        conf = yaml.load(c.read())

    env_name = env['ENV_NAME']
    image_path = env['IMAGE_PATH']
    slaves_count = int(env['SLAVES_COUNT'])

    conf['env_name'] = env_name
    node_params = conf['rack-01-node-params']
    node_params['volumes'][0]['source_image'] = image_path

    group = conf['groups'][0]
    for i in range(slaves_count):
        group['nodes'].append({'name': 'slave-{}'.format(i),
                               'role': 'slave'})
    for node in group['nodes']:
        node['params'] = node_params
    return {'template': {'devops_settings': conf}}

def get_ips(env):
    admin=env.get_node(role='master')
    return admin.get_ip_address_by_network_name('public')

def define_from_config(conf):
    env = Environment.create_environment(conf)
    env.start()
    print get_ips(env)


if __name__ == '__main__':
    config = create_config()
    define_from_config(config)
