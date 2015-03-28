"""
This handler required for custom modification for the networks resource.

It will create all required tasks for things like ovs/linux network
entities.
"""

from tool.resoure_handlers import base


class NetworkSchema(base.BaseResource):

    def __init__(self, parameters):
        pass

    def add_bridge(self, bridge):
        return 'shell: ovs-vsctl add-br {0}'.format(bridge)

    def add_port(self, bridge, port):
        return 'shell: ovs-vsctl add-port {0} {1}'.format(bridge, port)
