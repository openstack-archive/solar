from solar.core.log import log
from solar.core.transports.ssh import (SSHSyncTransport,
                                       SSHRunTransport)
from solar.core.transports.base import SyncTransport, Executor

# from functools import partial
# from itertools import takewhile
from collections import defaultdict
from operator import attrgetter, itemgetter

import libtorrent as lt
import os
from uuid import uuid4


# TODO: settings?
# TRACKERS = ['udp://192.168.4.140:8000',
#             'http://192.168.4.140:8000/announce']

TRACKERS = ['http://tracker01-bud.infra.mirantis.net:8080']


# def common_path(paths, sep=os.path.sep):
#     dirs = zip(*(p for p in paths))
#     return [x[0] for x in takewhile(lambda x: all(n == x[0] for n in x[1:]), dirs)]


# def prepare_paths(paths):
#     sep=os.path.sep
#     _deny_common = ('', '/')
#     _deny_common = [x.split(sep) for x in _deny_common]
#     paths = sorted(x.split(sep) for x in paths)
#     parents = []
#     current = paths[0]
#     parents.append(current)
#     for path in paths[1:]:
#         cp = common_path((parents[-1], path))
#         if cp not in _deny_common:
#             parents[-1] = cp
#         else:
#             parents.append(path)
#     return map(sep.join, parents)


class TorrentSyncTransport(SyncTransport):

    def __init__(self):
        super(TorrentSyncTransport, self).__init__()
        # we need some non torrent based sync transfer to upload client
        self._sync_helper = SSHSyncTransport()
        self._torrents = []
        self._sudo_torrents = []
        self._torrent_path = '/vagrant/torrents'

    def bind_with(self, other):
        self._sync_helper.bind_with(other)
        super(TorrentSyncTransport, self).bind_with(other)

    def copy(self, resource, _from, _to, use_sudo=False):
        log.debug("TORRENT: %s -> %s", _from, _to)

        executor = Executor(resource=resource,
                            executor=None,
                            params=(_from, _to, use_sudo))
        self.executors.append(executor)

    def _create_single_torrent(self, resource, _from, _to, use_sudo):
        fs = lt.file_storage()
        lt.add_files(fs, _from)
        self._create_torrent(resource, fs, _from)

    def _create_torrent_name(self):
        return os.path.join(self._torrent_path, uuid4().hex + '.torrent')

    def _create_torrent(self, resource, fs, root='.', use_sudo=False):
        t = lt.create_torrent(fs)
        for tracker in TRACKERS:
            t.add_tracker(tracker)
        lt.set_piece_hashes(t, os.path.join(root, '..'))
        torrent = t.generate()
        torrent['priv'] = True  # private torrent, no DHT, only trackers
        name = self._create_torrent_name()
        with open(name, 'wb') as f:
            f.write(lt.bencode(torrent))
        log.debug("Created torrent file %s", name)
        magnet_uri = lt.make_magnet_uri(lt.torrent_info(name))
        # self._torrents[root] = (name, magnet_uri)
        if not use_sudo:
            self._torrents.append((name, magnet_uri, root))
        else:
            self._sudo_torrents.append((name, magnet_uri, root))
        return name

    def _start_seeding(self):
        # XXX: naive naive naive
        # we don't need use sudo there for now
        from fabric import api as fabric_api
        torrents = self._torrents + self._sudo_torrents
        to_seed = ["%s|%s" % (os.path.abspath(os.path.join(x[2], '..')), x[0]) for x in torrents]
        seed_args = ';'.join(to_seed)
        # TODO: 'g' is just for debug, it should be 's', remove when sure
        cmd = ['/usr/bin/python',
               '/vagrant/solar/solar/core/transports/helpers/solar_torrent.py',
               'g',
               '"%s"' % seed_args]
        log.debug("Will start seeding: %r" % ' '.join(cmd))
        fabric_api.local(' '.join(cmd))
        log.debug("Torrent seeding started")

    def _start_remote_fetch(self, resource, use_sudo):
        # later we will send solar_torrent with other sync tranport,
        # or remote will have solar_torrent installed somehow
        if use_sudo is False:
            torrents = self._torrents
        else:
            torrents = self._sudo_torrents
        to_get = ["%s|%s" % (os.path.abspath(os.path.join(x[2], '..')), x[1]) for x in torrents]
        get_args = ';'.join(to_get)
        cmd = ['/usr/bin/python',
               '/var/tmp/solar_torrent.py',
               'g',
               '"%s"' % get_args]
        self.other(resource).run(resource, *cmd, use_sudo=use_sudo)

    def other(self, resource):
        # TODO: implement it
        pass

    def preprocess(self, executor):
        _from, _to, use_sudo = executor.params
        self._create_single_torrent(executor.resource, _from, _to, use_sudo)

    def run_all(self):
        self._start_seeding()
        resource = self.executors[0].resource
        # TODO: we should paralelize it
        if self._torrents:
            self._start_remote_fetch(resource, use_sudo=False)
        if self._sudo_torrents:
            self._start_remote_fetch(resource, use_sudo=True)

