
from collections import defaultdict

import inspect

from functools import partial

from solar.core.log import log


class SubControl(object):

    def on_success(self, sub):
        self.add_subscriber(sub, 'on_success')

    def on_error(self, sub):
        self.add_subscriber(sub, 'on_error')

    def after(self, sub):
        self.add_subscriber(sub, 'after')

    def before(self, sub):
        self.add_subscriber(sub, 'before')

    def add_subscriber(self, sub, event):
        raise NotImplemented()


class FuncSubControl(SubControl):

    def __init__(self, instance, func):
        self.instance = instance
        self.func = func
        self._subscribers = defaultdict(list)
        self.__name__ = func.__name__

    def add_subscriber(self, subscriber, event):
        """
        :param target_func: string or function object
        :param subscriber: callable
        :param events: None or iterable
        """
        self._subscribers[event].append(subscriber)

    def __call__(self, ctxt, *args, **kwargs):
        for sub in self._subscribers['before']:
            try:
                sub()
            except Exception as exc:
                log.warning('Subscriber %r failed with %s', sub, exc)
        try:
            rst = self.func(self.instance, ctxt, *args, **kwargs)
            for sub in self._subscribers['on_success']:
                try:
                    sub(ctxt, rst, *args, **kwargs)
                except Exception as exc:
                    log.warning('Subscriber %r failed with %s', sub, exc)
            return rst
        except Exception as exc:
            for sub in self._subscribers['on_error']:
                try:
                    sub(ctxt, exc, *args, **kwargs)
                except Exception as exc:
                    log.warning('Subscriber %r failed with %s', sub, exc)
            raise
        finally:
            for sub in self._subscribers['after']:
                try:
                    sub()
                except Exception as exc:
                    log.warning('Subscriber %r failed with %s', sub, exc)


class FuncSub(object):

    def __init__(self, func):
        self.func = func

    def __get__(self, obj, owner):
        property_name = '__sub_control_' + self.func.__name__
        sub_control = getattr(obj, property_name, None)
        if not sub_control:
            setattr(obj, property_name, FuncSubControl(obj, self.func))
        return getattr(obj, property_name)


class CollectionSubControl(SubControl):

    def __init__(self, instance):
        self.instance = instance

    def add_subscriber(self, subscriber, event):
        for entity_name, entity in inspect.getmembers(self.instance):
            if isinstance(entity, FuncSubControl) and entity_name[:2] != '__':
                entity.add_subscriber(subscriber, event)


class CollectionSub(object):

    def __get__(self, obj, owner):
        return CollectionSubControl(obj)
