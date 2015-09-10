
from pytest import fixture

from solar.system_log import data

@fixture
def host_diff():
    return [
        [u'add', u'', [
            [u'ip', u'10.0.0.3'],
            [u'hosts_names', ['riak_server1.solar', 'riak_server2.solar', 'riak_server3.solar']],
            [u'ssh_user', u'vagrant'],
            [u'ssh_key', u'/vagrant/.vagrant/machines/solar-dev1/virtualbox/private_key'],
    ]]]


def test_details_for_add(host_diff):
    assert data.details(host_diff) == [
        '++ ip: 10.0.0.3',
        "++ hosts_names: ['riak_server1.solar', 'riak_server2.solar', 'riak_server3.solar']",
        '++ ssh_user: vagrant', '++ ssh_key: /vagrant/.vagrant/machines/solar-dev1/virtualbox/private_key']


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
