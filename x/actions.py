# -*- coding: UTF-8 -*-
import handlers


def resource_action(resource, action):
    handler = resource.metadata['handler']
    with handlers.get(handler)([resource]) as h:
        h.action(resource, action)


def tag_action(tag, action):
    #TODO
    pass
