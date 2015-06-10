
import os

from pytest import fixture

from solar.interfaces import db
from solar import utils


def pytest_configure():
    db.DB = db.mapping['fakeredis_db']()


@fixture(autouse=True)
def cleanup(request):

    def fin():
        from solar.core import signals

        db.get_db().clear()
        signals.Connections.clear()

    request.addfinalizer(fin)



@fixture
def default_resources():
    from solar.core import signals
    from solar.core import resource
    node1 = resource.create('node1', '/vagrant/resources/ro_node/', {'ip': '10.0.0.3', 'ssh_key': '/vagrant/.vagrant/machines/solar-dev1/virtualbox/private_key', 'ssh_user': 'vagrant'})

    rabbitmq_service1 = resource.create('rabbitmq', '/vagrant/resources/rabbitmq_service/', {'ssh_user': '', 'ip': '','management_port': '15672', 'port': '5672', 'ssh_key': '', 'container_name': 'rabbitmq_service1', 'image': 'rabbitmq:3-management'})
    openstack_vhost = resource.create('vhost', '/vagrant/resources/rabbitmq_vhost/', {'ssh_user': '', 'ip': '', 'ssh_key': '', 'vhost_name': 'openstack', 'container_name': ''})
    signals.connect(node1, rabbitmq_service1)
    signals.connect(rabbitmq_service1, openstack_vhost)
    return resource.load_all()
