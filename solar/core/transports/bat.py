from solar.core.transports.base import SyncTransport, RunTransport, SolarTransport
from solar.core.transports.ssh import SSHSyncTransport, SSHRunTransport
from solar.core.transports.rsync import RsyncSyncTransport
try:
    from solar.core.transports.solar_agent_transport import SolarAgentRunTransport, SolarAgentSyncTransport
except ImportError:
    _solar_agent_available = False
else:
    _solar_agent_available = True

try:
    from solar.core.transports.torrent import TorrentSyncTransport
except ImportError:
    _torrent_available = False
else:
    _torrent_available = True


KNOWN_SYNC_TRANSPORTS = {
    'rsync': RsyncSyncTransport,
    'ssh': SSHSyncTransport
}


KNOWN_RUN_TRANSPORTS = {
    'ssh': SSHRunTransport
}


if _torrent_available:
    KNOWN_SYNC_TRANSPORTS['torrent'] = TorrentSyncTransport
if _solar_agent_available:
    KNOWN_SYNC_TRANSPORTS['solar_agent'] = SolarAgentSyncTransport
    KNOWN_RUN_TRANSPORTS['solar_agent'] = SolarAgentRunTransport


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
            for pref in self._order:
                selected = next((x for x in transports if x['name'] == pref), None)
                if selected:
                    break
            if not selected:
                raise Exception("No valid transport found")
            instance = self._bat_transports[selected['name']]()
            setattr(resource, '_used_transport_%s' % instance._mode, selected)
            setattr(resource, key_name, instance)
            self._used_transports.append(instance)
            instance.bind_with(self._other_remember)
            return instance
            # return self._bat_transports[selected['name']]

    def get_transport_data(self, resource, *args, **kwargs):
        self.select_valid_transport(resource)
        return super(BatTransport, self).get_transport_data(resource, *args, **kwargs)

    def bind_with(self, other):
        self._other_remember = other


class BatSyncTransport(SyncTransport, BatTransport):

    preffered_transport_name = None
    _order = ('torrent', 'solar_agent', 'rsync', 'ssh')
    _bat_transports = KNOWN_SYNC_TRANSPORTS

    def __init__(self, *args, **kwargs):
        BatTransport.__init__(self)
        SyncTransport.__init__(self, *args, **kwargs)

    def copy(self, resource, *args, **kwargs):
        transport = self.select_valid_transport(resource)
        return transport.copy(resource, *args, **kwargs)

    run_all = OnAll('run_all')
    preprocess_all = OnAll('preprocess_all')


class BatRunTransport(RunTransport, BatTransport):

    preffered_transport_name = None
    _order = ('solar_agent', 'ssh')
    _bat_transports = KNOWN_RUN_TRANSPORTS

    def __init__(self, *args, **kwargs):
        BatTransport.__init__(self)
        RunTransport.__init__(self, *args, **kwargs)

    def run(self, resource, *args, **kwargs):
        transport = self.select_valid_transport(resource)
        return transport.run(resource, *args, **kwargs)
