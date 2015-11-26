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

import handlers

# from solar.core.transports.ssh import SSHSyncTransport, SSHRunTransport
# from solar.core.transports.rsync import RsyncSyncTransport
# from solar.core.transports.solar_agent_transport import SolarAgentRunTransport, SolarAgentSyncTransport

from solar.core.transports.bat import BatRunTransport, BatSyncTransport

_default_transports = {
    # 'sync': RsyncSyncTransport,
    # 'sync': SSHSyncTransport,
    # 'run': SSHRunTransport,
    # 'run': SolarAgentRunTransport,
    # 'sync': SolarAgentSyncTransport
    'run': BatRunTransport,
    'sync': BatSyncTransport
}


def resource_action(resource, action):
    handler = resource.db_obj.handler or 'none'
    with handlers.get(handler)([resource], _default_transports) as h:
        return h.action(resource, action)


def tag_action(tag, action):
    # TODO
    pass
