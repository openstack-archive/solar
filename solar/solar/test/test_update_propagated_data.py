import pytest
from mock import patch

from solar.core import signals
from solar.core import resource
from solar import operations
from solar import state

@pytest.fixture
def resources():

    node1 = resource.create('node1', '/vagrant/resources/ro_node/', {'ip': '10.0.0.3', 'ssh_key': '/vagrant/', 'ssh_user': 'vagrant'})

    mariadb_service1 = resource.create('mariadb', '/vagrant/resources/mariadb_service', {'image': 'mariadb', 'root_password': 'mariadb', 'port': 3306, 'ip': '', 'ssh_user': '', 'ssh_key': ''})
    keystone_db = resource.create('keystone_db', '/vagrant/resources/mariadb_keystone_db/', {'db_name': 'keystone_db', 'login_password': '', 'login_user': 'root', 'login_port': '', 'ip': '', 'ssh_user': '', 'ssh_key': ''})

    signals.connect(node1, mariadb_service1)
    signals.connect(node1, keystone_db)
    signals.connect(mariadb_service1, keystone_db, {'root_password': 'login_password', 'port': 'login_port'})
    return resource.load_all()


@patch('solar.core.actions.resource_action')
def test_update_port_on_mariadb(maction, resources):
    operations.stage_changes()
    operations.commit_changes()

    mariadb = resources['mariadb']

    mariadb.update({'port': 4400})

    log = operations.stage_changes()

    assert len(log) == 2

    mariadb_log = log.items[0]

    assert mariadb_log.diff == [
        ('change', u'input.port.value', (3306, 4400)),
        ('change', u'metadata.input.port.value', (3306, 4400))]

    keystone_db_log = log.items[1]

    assert keystone_db_log.diff == [
        ('change', u'input.login_port.value', (3306, 4400)),
        ('change', u'metadata.input.login_port.value', (3306, 4400))]


@pytest.fixture
def list_input():
    res1 = resource.wrap_resource(
        {'id': 'res1', 'input': {'ip': {'value': '10.10.0.2'}}})
    res1.save()
    res2 = resource.wrap_resource(
        {'id': 'res2', 'input': {'ip': {'value': '10.10.0.3'}}})
    res2.save()
    consumer = resource.wrap_resource(
        {'id': 'consumer', 'input':
            {'ips': {'value': [],
                     'schema': ['str']}}})
    consumer.save()

    signals.connect(res1, consumer, {'ip': 'ips'})
    signals.connect(res2, consumer, {'ip': 'ips'})
    return resource.load_all()


@patch('solar.core.actions.resource_action')
def test_update_list_resource(maction, list_input):
    operations.stage_changes()
    operations.commit_changes()

    res3 = resource.wrap_resource(
        {'id': 'res3', 'input': {'ip': {'value': '10.10.0.4'}}})
    res3.save()
    signals.connect(res3, list_input['consumer'], {'ip': 'ips'})

    log = operations.stage_changes()

    assert len(log) == 2

    assert log.items[0].res == res3.name
    assert log.items[1].diff == [
        ('add', u'connections', [(2, ['res3', u'consumer', ['ip', 'ips']])]),
        ('add', u'input.ips', [
            (2, {u'emitter_attached_to': u'res3', u'emitter': u'ip', u'value': u'10.10.0.4'})]),
        ('add', u'metadata.input.ips.value',
            [(2, {u'emitter_attached_to': u'res3', u'emitter': u'ip', u'value': u'10.10.0.4'})])]

    operations.commit_changes()
    assert list_input['consumer'].args_dict() == {
            u'ips': [
                {u'emitter_attached_to': u'res1', u'emitter': u'ip', u'value': u'10.10.0.2'},
                {u'emitter_attached_to': u'res2', u'emitter': u'ip', u'value': u'10.10.0.3'},
                {'emitter_attached_to': 'res3', 'emitter': 'ip', 'value': '10.10.0.4'}]}

    log_item = operations.rollback_last()
    assert log_item.diff == [
        ('remove', u'connections', [(2, ['res3', u'consumer', ['ip', 'ips']])]),
        ('remove', u'input.ips', [
            (2, {u'emitter_attached_to': u'res3', u'emitter': u'ip', u'value': u'10.10.0.4'})]),
        ('remove', u'metadata.input.ips.value',
            [(2, {u'emitter_attached_to': u'res3', u'emitter': u'ip', u'value': u'10.10.0.4'})])]

    consumer = resource.load('consumer')
    assert consumer.args_dict() == {
        u'ips': [{u'emitter': u'ip',
                  u'emitter_attached_to': u'res1',
                  u'value': u'10.10.0.2'},
                 {u'emitter': u'ip',
                  u'emitter_attached_to': u'res2',
                  u'value': u'10.10.0.3'}]}


