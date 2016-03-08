#    Copyright 2016 Mirantis, Inc.
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

import mock

import pytest

from solar.core.transports.bat import BatRunTransport


@mock.patch('solar.core.resource.resource.Resource.transports')
def test_bat_run_transport(mock_transports, resources):
    mock_transports.return_value = [
        {'key': u'private_key',
         'name': u'ssh',
         'password': None,
         'port': 22,
         'user': u'user'}]

    node = resources['node1']

    transport = BatRunTransport()
    transport.run(node)

    assert transport._order == ['ssh']


@mock.patch('solar.core.resource.resource.Resource.transports')
def test_bat_run_transport_nonexistent(mock_transports, resources):
    mock_transports.return_value = [{'name': u'no_such_transport'}]

    node = resources['node1']

    transport = BatRunTransport()
    with pytest.raises(Exception) as excinfo:
        transport.run(node)
    assert 'No valid transport found' in excinfo.value
