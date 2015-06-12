
import pytest
from mock import patch

from solar.core import resource
from solar import operations
from solar import state


@pytest.fixture
def default_resources():
    from solar.core import signals
    from solar.core import resource

    node1 = resource.wrap_resource(
        {'id': 'node1',
         'input': {'ip': {'value':'10.0.0.3'}}})
    rabbitmq_service1 = resource.wrap_resource(
        {'id':'rabbitmq', 'input': {
            'ip' : {'value': ''},
            'image': {'value': 'rabbitmq:3-management'}}})
    signals.connect(node1, rabbitmq_service1)
    return resource.load_all()


@patch('solar.core.actions.resource_action')
@pytest.mark.usefixtures("default_resources")
def test_changes_on_update_image(maction):
    log = operations.stage_changes()

    assert len(log) == 2

    operations.commit_changes()

    rabbitmq = resource.load('rabbitmq')
    rabbitmq.update({'image': 'different'})
    log = operations.stage_changes()

    assert len(log) == 1

    item = log.items[0]

    assert item.diff == [
        ('change', u'input.image.value',
            (u'rabbitmq:3-management', u'different')),
        ('change', u'metadata.input.image.value',
            (u'rabbitmq:3-management', u'different'))]

    assert item.action == 'update'

    operations.commit_changes()

    commited = state.CD()

    assert commited['rabbitmq']['input']['image'] == {
        u'emitter': None, u'value': u'different'}

    reverse = operations.rollback(state.CL().items[-1])

    assert reverse.diff == [
        ('change', u'input.image.value',
            (u'different', u'rabbitmq:3-management')),
        ('change', u'metadata.input.image.value',
            (u'different', u'rabbitmq:3-management'))]

    operations.commit_changes()

    commited = state.CD()

    assert commited['rabbitmq']['input']['image'] == {
        u'emitter': None, u'value': u'rabbitmq:3-management'}




