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


from stevedore.extension import ExtensionManager

from solar.core.transports.base import RunTransport
from solar.core.transports.base import SolarTransport
from solar.core.transports.base import SyncTransport

from operator import itemgetter


TRANSPORTS_DATA = {
    'run': {'transports': {}, 'order': []},
    'sync': {'transports': {}, 'order': []}
}


class FilteredExtensionManager(ExtensionManager):
    def __init__(self, namespace, filter_func, *args, **kwargs):
        self.filter_func = filter_func
        super(FilteredExtensionManager, self).__init__(
            namespace, *args, **kwargs
        )

    def _find_entry_points(self, namespace):
        eps = super(FilteredExtensionManager, self)._find_entry_points(
            namespace)
        return [ep for ep in eps if self.filter_func(ep)]


def _find_transports(mode, wanted_transports):
    transports_data = TRANSPORTS_DATA[mode]

    def filter_entry_point(entry_point):
        is_preferred = any(
            entry_point.name == wt['name']
            for wt in wanted_transports)

        is_loaded = entry_point.name in (
            t for t in transports_data['transports'].keys()
        )

        return is_preferred and not is_loaded

    mgr = FilteredExtensionManager(
        namespace='solar.transports.%s' % mode,
        filter_func=filter_entry_point
    )

    extensions = mgr.extensions
    new_transports = dict(map(lambda x: (x.name, x.plugin), extensions))
    transports_data['transports'].update(new_transports)
    orders = [(getattr(plugin, '_priority', -1), name)
              for name, plugin in transports_data['transports'].iteritems()]
    transports_data['order'] = map(itemgetter(1),
                                   sorted(orders, reverse=True))

    transports = {k: v for (k, v) in
                  transports_data['transports'].iteritems()
                  if any(k == wt['name']
                         for wt in wanted_transports)}
    order = [
        x for x in transports_data['order']
        if any(x == wt['name']
               for wt in wanted_transports)
    ]
    return transports, order


class OnAll(object):

    def __init__(self, target):
        self._target = target

    def __get__(self, obj, objtype):
        def _inner(*args, **kwargs):
            for transport in obj._used_transports:
                getattr(transport, self._target)(*args, **kwargs)
        return _inner


class BatTransport(SolarTransport):

    _order = ()
    _transport_mode = ''

    def __init__(self, *args, **kwargs):
        super(BatTransport, self).__init__(*args, **kwargs)
        self._cache = {}
        self._used_transports = []
        self._other_remember = None

    def select_valid_transport(self, resource, *args, **kwargs):
        key_name = '_bat_transport_%s' % self._mode
        try:
            return getattr(resource, key_name)
        except AttributeError:
            transports = resource.transports()

            self._bat_transports, self._order = _find_transports(
                self._transport_mode, transports)

            if len(self._order) == 0:
                raise Exception("No valid transport found")
            selected = self._bat_transports[self._order[0]]
            if not selected:
                raise Exception("No valid transport found")

            instance = selected()
            selected_transport_data = next(t for t in transports
                                           if t['name'] == self._order[0])
            setattr(resource, '_used_transport_%s' % instance._mode,
                    selected_transport_data)
            setattr(resource, key_name, instance)
            self._used_transports.append(instance)
            instance.bind_with(self._other_remember)
            return instance

    def get_transport_data(self, resource, *args, **kwargs):
        self.select_valid_transport(resource)
        return super(BatTransport, self).get_transport_data(resource,
                                                            *args, **kwargs)

    def bind_with(self, other):
        self._other_remember = other


class BatSyncTransport(SyncTransport, BatTransport):

    preferred_transport_name = None
    _transport_mode = 'sync'

    def __init__(self, *args, **kwargs):
        BatTransport.__init__(self)
        SyncTransport.__init__(self, *args, **kwargs)

    def copy(self, resource, *args, **kwargs):
        transport = self.select_valid_transport(resource)
        return transport.copy(resource, *args, **kwargs)

    run_all = OnAll('run_all')
    preprocess_all = OnAll('preprocess_all')


class BatRunTransport(RunTransport, BatTransport):

    preferred_transport_name = None
    _transport_mode = 'run'

    def __init__(self, *args, **kwargs):
        BatTransport.__init__(self)
        RunTransport.__init__(self, *args, **kwargs)

    def run(self, resource, *args, **kwargs):
        transport = self.select_valid_transport(resource)
        return transport.run(resource, *args, **kwargs)
