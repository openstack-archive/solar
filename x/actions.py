# -*- coding: UTF-8 -*-
import handlers

def resource_action(resource, action):
    handler = resource.metadata['handler']
    handler = handlers.get(handler)
    handler().action(resource, action)

def tag_action(tag, action):
    #TODO
    pass
