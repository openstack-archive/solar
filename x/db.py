# -*- coding: UTF-8 -*-

RESOURCE_DB = {}


def resource_add(key, value):
    if key in RESOURCE_DB:
        raise Exception('Key `{0}` already exists'.format(key))
    RESOURCE_DB[key] = value


def get_resource(key):
    return RESOURCE_DB.get(key, None)


def clear():
    global RESOURCE_DB

    RESOURCE_DB = {}
