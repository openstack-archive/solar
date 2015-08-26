# -*- coding: utf-8 -*-
import handlers

from solar.core.transports.ssh import SSHSyncTransport, SSHRunTransport

_default_transports = {
    'sync': SSHSyncTransport,
    'run': SSHRunTransport
}

def resource_action(resource, action):
    handler = resource.metadata.get('handler', 'none')
    with handlers.get(handler)([resource]) as h:
        return h.action(resource, action)


def tag_action(tag, action):
    #TODO
    pass
