# -*- coding: UTF-8 -*-
import handlers


def resource_action(resource, action):
    handler = resource.metadata['handler']
    with handlers.get(handler)([resource]) as h:
        return h.action(resource, action)


def tag_action(tag, action):
    #TODO
    pass
