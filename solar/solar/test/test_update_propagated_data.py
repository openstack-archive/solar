import pytest

from solar.core import signals
from solar.core import resource
from solar import operations

@pytest.fixture
def resources():

    node1 = resource.wrap_resource(
        {'id': 'node1',
         'input': {'ip': {'value': '10.0.0.3'}}})
    mariadb_service1 = resource.wrap_resource(
        {'id': 'mariadb', 'input': {
            'port' : {'value': 3306},
            'ip': {'value': ''}}})
    keystone_db = resource.wrap_resource(
        {'id':'keystone_db',
         'input': {
            'login_port' : {'value': ''},
            'ip': {'value': ''}}})
    signals.connect(node1, mariadb_service1)
    signals.connect(node1, keystone_db)
    signals.connect(mariadb_service1, keystone_db, {'port': 'login_port'})
    return resource.load_all()


def test_update_port_on_mariadb(resources):
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
    res2 = resource.wrap_resource(
        {'id': 'res2', 'input': {'ip': {'value': '10.10.0.3'}}})
    consumer = resource.wrap_resource(
        {'id': 'consumer', 'input':
            {'ips': {'value': [],
                     'schema': ['str']}}})

    signals.connect(res1, consumer, {'ip': 'ips'})
    signals.connect(res2, consumer, {'ip': 'ips'})
    return resource.load_all()


def test_update_list_resource(list_input):
    operations.stage_changes()
    operations.commit_changes()

    res3 = resource.wrap_resource(
        {'id': 'res3', 'input': {'ip': {'value': '10.10.0.4'}}})

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
                {u'emitter_attached_to': u'res3', u'emitter': u'ip', u'value': u'10.10.0.4'}]}

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


