# -*- coding: utf-8 -*-
#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import os
from StringIO import StringIO

import pytest
import yaml

from solar.core.resource import virtual_resource as vr
from solar.events.controls import Dep
from solar.events.controls import React


@pytest.fixture
def good_events():
    events = '''
  - type: depends_on
    parent_action: 'service1.run'
    state: 'success'
    depend_action: 'config1.run'
  - type: react_on
    parent_action: 'config1.run'
    state: 'success'
    depend_action: 'service1.apply_config'
'''
    return yaml.load(StringIO(events))


@pytest.fixture
def bad_event_type():
    events = '''
  - type: skip
    parent_action: 'service1.run'
    state: 'success'
    depend_action: 'config1.run'
'''
    return yaml.load(StringIO(events))


def test_create_path_does_not_exists():
    with pytest.raises(Exception) as excinfo:
        vr.create('node1', '/path/does/not/exists')
    err = 'Base resource does not exist: /path/does/not/exists'
    assert str(excinfo.value) == err


def test_create_resource():
    node_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'resource_fixtures', 'node')
    resources = vr.create('node1', node_path)
    assert len(resources) == 1
    assert resources[0].name == 'node1'


def test_create_virtual_resource(tmpdir):
    base_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'resource_fixtures')
    vr_tmpl_path = os.path.join(base_path, 'nodes.yaml.tmpl')
    node_resource_path = os.path.join(base_path, 'node')
    with open(vr_tmpl_path) as f:
        vr_data = f.read().format(resource_path=node_resource_path)
    vr_file = tmpdir.join('nodes.yaml')
    vr_file.write(vr_data)
    resources = vr.create('nodes', str(vr_file))
    assert len(resources) == 2


def test_create_virtual_resource_with_list(tmpdir):
    base_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'resource_fixtures')
    vr_tmpl_path = os.path.join(base_path, 'resource_with_list.yaml.tmpl')
    base_resource_path = os.path.join(base_path, 'base_service')
    with open(vr_tmpl_path) as f:
        vr_data = f.read().format(resource_path=base_resource_path)
    vr_file = tmpdir.join('base.yaml')
    vr_file.write(vr_data)
    resources = vr.create('base', str(vr_file))
    assert len(resources) == 1
    res = resources[0]
    assert res.args['servers'] == [1, 2]


def test_update(tmpdir):
    # XXX: make helper for it
    base_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'resource_fixtures')
    vr_node_tmpl_path = os.path.join(base_path, 'nodes.yaml.tmpl')
    vr_update_tmpl_path = os.path.join(base_path, 'update.yaml.tmpl')
    update_path = os.path.join(base_path, 'update')
    node_resource_path = os.path.join(base_path, 'node')
    with open(vr_node_tmpl_path) as f:
        vr_data = f.read().format(resource_path=node_resource_path)
    with open(vr_update_tmpl_path) as f:
        update_data = f.read().format(resource_path=update_path)
    vr_file = tmpdir.join('nodes.yaml')
    vr_file.write(vr_data)
    update_file = tmpdir.join('update.yaml')
    update_file.write(update_data)
    resources = vr.create('nodes', str(vr_file))
    vr.create('updates', str(update_file))
    assert resources[0].args['ip'] == '10.0.0.4'


def test_parse_events(good_events):
    events = [Dep(parent='service1', parent_action='run',
                  child='config1', child_action='run',
                  state='success'),
              React(parent='config1', parent_action='run',
                    child='service1', child_action='apply_config',
                    state='success')]
    parsed = vr.parse_events(good_events)
    assert events == parsed


def test_parse_bad_event(bad_event_type):
    with pytest.raises(Exception) as execinfo:
        vr.parse_events(bad_event_type)
    error = 'Invalid event type: skip'
    assert error == str(execinfo.value)


def test_add_connections(mocker, resources):
    mocked_signals = mocker.patch(
        'solar.core.resource.resource.Resource.connect_with_events')
    args = {'ip': 'node1::ip',
            'servers': ['node1::ip', 'node2::ip'],
            'alias': 'ser1'
            }
    vr.update_inputs('service1', args)
    assert mocked_signals.call_count == 2


def test_add_list_values(mocker, resources):
    mocked_signals = mocker.patch(
        'solar.core.resource.resource.Resource.connect_with_events')
    args = {'ip': 'node1::ip',
            'servers': ['server1', 'server2'],
            'alias': 'ser1'
            }
    vr.update_inputs('service1', args)
    assert mocked_signals.call_count == 1


def test_parse_connection():
    correct_connection = {'child_input': 'ip',
                          'parent': 'node1',
                          'parent_input': 'ip',
                          'events': None
                          }
    connection = vr.parse_connection('ip', 'node1::ip')
    assert correct_connection == connection


def test_parse_connection_disable_events():
    correct_connection = {'child_input': 'ip',
                          'parent': 'node1',
                          'parent_input': 'ip',
                          'events': False
                          }
    connection = vr.parse_connection('ip', 'node1::ip::NO_EVENTS')
    assert correct_connection == connection


def test_setting_location(tmpdir):
    # XXX: make helper for it
    base_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'resource_fixtures')
    vr_node_tmpl_path = os.path.join(base_path, 'nodes.yaml.tmpl')
    vr_location_tmpl_path = os.path.join(base_path, 'with_location.yaml.tmpl')
    base_service_path = os.path.join(base_path, 'base_service')
    node_resource_path = os.path.join(base_path, 'node')
    with open(vr_node_tmpl_path) as f:
        vr_data = f.read().format(resource_path=node_resource_path)
    with open(vr_location_tmpl_path) as f:
        location_data = f.read().format(resource_path=base_service_path)
    vr_file = tmpdir.join('nodes.yaml')
    vr_file.write(vr_data)
    location_file = tmpdir.join('with_location.yaml')
    location_file.write(location_data)
    vr.create('nodes', str(vr_file))
    resources = vr.create('updates', str(location_file))
    assert 'location=node1' in resources[0].tags
