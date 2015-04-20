# Deploying stuff from YAML definition

import imp
import os
import shutil
import yaml

#from x import actions as xa
from x import db
from x import resource as xr
from x import signals as xs


def deploy(filename):
    with open(filename) as f:
        config = yaml.load(f)

    workdir = config['workdir']
    resource_save_path = os.path.join(workdir, config['resource-save-path'])

    # Clean stuff first
    clients_file = os.path.join(workdir, 'clients.json')
    if os.path.exists(clients_file):
        os.remove(clients_file)
    shutil.rmtree(resource_save_path, ignore_errors=True)
    os.makedirs(resource_save_path)

    # Create resources first
    for resource_definition in config['resources']:
        name = resource_definition['name']
        model = os.path.join(workdir, resource_definition['model'])
        args = resource_definition.get('args', {})
        print 'Creating ', name, model, resource_save_path, args
        xr.create(name, model, resource_save_path, args=args)

    # Create resource connections
    for connection in config['connections']:
        emitter = db.get_resource(connection['emitter'])
        receiver = db.get_resource(connection['receiver'])
        mapping = config.get('mapping')
        print 'Connecting ', emitter.name, receiver.name, mapping
        xs.connect(emitter, receiver, mapping=mapping)

    # Run all tests
    if 'test-suite' in config:
        #test_suite_path = os.path.join(workdir, config['test-suite'])
        print 'Running tests from {}'.format(config['test-suite'])
        #test_suite = imp.load_source('main', test_suite_path)
        test_suite = __import__(config['test-suite'], {}, {}, ['main'])
        test_suite.main()
