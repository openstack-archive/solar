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

from pytest import fixture

from solar.system_log import data


@fixture
def host_diff():
    return [
        [u'add', u'', [
            [u'ip', {u'emitter': u'node1', u'value': u'10.0.0.3'}],
            [u'hosts_names',
                [{u'emitter_attached_to': u'riak_service1', u'emitter': u'riak_hostname', u'value': u'riak_server1.solar'},
                 {u'emitter_attached_to': u'riak_service2', u'emitter': u'riak_hostname', u'value': u'riak_server2.solar'},
                 {u'emitter_attached_to': u'riak_service3', u'emitter': u'riak_hostname', u'value': u'riak_server3.solar'}]],
            [u'ssh_user', {u'emitter': None, u'value': u'vagrant'}],
            [u'ssh_key', {u'emitter': u'node1', u'value': u'/vagrant/.vagrant/machines/solar-dev1/virtualbox/private_key'}],
    ]]]


def test_details_for_add(host_diff):
    assert data.details(host_diff) == [
        '++ ip: node1::10.0.0.3',
        "++ hosts_names: ['riak_hostname::riak_server1.solar', 'riak_hostname::riak_server2.solar', 'riak_hostname::riak_server3.solar']",
        '++ ssh_user: vagrant', '++ ssh_key: node1::/vagrant/.vagrant/machines/solar-dev1/virtualbox/private_key']


@fixture
def list_change():
    return [[u'change', [u'configs_ports', 0, u'value', 0, u'value'], [18098, 88888]]]

def test_list_details_for_change(list_change):
    assert data.details(list_change) == ['-+ configs_ports:[0] : 18098 >> 88888']


@fixture
def single_change():
    return [[u'change', u'riak_port_http', [18098, 88888]]]


def test_single_details_for_change(single_change):
    assert data.details(single_change) == ['-+ riak_port_http: 18098 >> 88888']
