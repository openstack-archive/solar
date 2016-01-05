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

# TODO: change to something less naive
#

from __future__ import print_function

import libtorrent as lt
from operator import attrgetter
import os
import sys
import time

state_str = ['queued', 'checking', 'downloading metadata', 'downloading',
             'finished', 'seeding', 'allocating', 'checking fastresume']


# we use port range from 6881 to 6981


class MultiTorrent(object):
    def __init__(self, torrents, ses):
        self.torrents = torrents
        self.ses = ses

    def force_reannounce(self):
        for torrent in self.torrents:
            torrent.force_reannounce()

    @property
    def is_seeding(self):
        for torrent in self.torrents:
            status = torrent.status()
            if state_str[status.state] != 'seeding':
                return False
        return True

    @property
    def progress(self):
        total_progress = map(
            attrgetter('progress'), map(lambda x: x.status(), self.torrents))
        return sum(total_progress) / len(total_progress)

    def numbers(self):
        seeding = 0
        downloading = 0
        for torrent in self.torrents:
            if torrent.status().is_seeding:
                seeding += 1
            else:
                downloading += 1
        return seeding, downloading


def init_session(args, seed=False):
    ses = lt.session()
    all_torrents = []
    for save_path, magnet_or_path in args:
        if os.path.exists(magnet_or_path):
            e = lt.bdecode(open(magnet_or_path, 'rb').read())
            info = lt.torrent_info(e)
            params = {'save_path': save_path,
                      'storage_mode': lt.storage_mode_t.storage_mode_sparse,
                      'ti': info,
                      'seed_mode': seed}
            h = ses.add_torrent(params)
        else:
            h = ses.add_torrent({
                'save_path': save_path,
                'storage_mode': lt.storage_mode_t.storage_mode_sparse,
                'url': magnet_or_path,
                'seed_mode': seed
            })
        all_torrents.append(h)
    return ses, all_torrents


def _daemonize():
    # should be true daemonize
    new_pid = os.fork()
    if new_pid > 0:
        # first
        sys.exit(0)
    os.setsid()
    new_pid2 = os.fork()
    if new_pid2 > 0:
        sys.exit(0)
    stdin = file(os.devnull, 'r')
    stdout = file(os.devnull, 'a+')
    stderr = file(os.devnull, 'a+', 0)
    os.dup2(stdin.fileno(), sys.stdin.fileno())
    os.dup2(stdout.fileno(), sys.stdout.fileno())
    os.dup2(stderr.fileno(), sys.stderr.fileno())


def _seeder(torrents, save_path='.', max_seed_ratio=5):
    _daemonize()
    no_peers = 120
    max_alive = 5 * 60
    ses, all_torrents = init_session(torrents, seed=True)
    ses.listen_on(6881, 6981)

    mt = MultiTorrent(all_torrents, ses)
    end = time.time() + max_alive
    peers_0 = time.time()
    i = 0
    while not time.time() > end:
        now = time.time()
        i += 1
        # if i % 10 == 0 and i != 0:
        #     mt.force_reannounce()
        s = ses.status()
        # if not mt.is_seeding:
        #     sys.exit("Was seeder mode but not seeding")
        if peers_0 < now - no_peers:
            sys.exit("No peers for %d seconds exiting" % no_peers)
        if i % 5 == 0:
            print("%.2f%% up=%.1f kB/s peers=%s total_upload_B=%.1f" %
                  (mt.progress * 100, s.upload_rate / 1000, s.num_peers,
                   s.total_upload))
        if s.num_peers != 0:
            peers_0 = now
        sys.stdout.flush()
        time.sleep(1)
    else:
        print('Seed timeout exiting')
    sys.exit(0)


def _getter(torrents, max_seed_ratio=3):
    max_no_changes = 1 * 60
    ses, all_torrents = init_session(torrents)
    ses.listen_on(6881, 6981)

    mt = MultiTorrent(all_torrents, ses)

    i = 0
    last_state = (time.time(), None)
    while (not mt.is_seeding):
        i += 1
        # if i % 10 == 0 and i != 0:
        #     mt.force_reannounce()
        s = ses.status()
        if i % 5 == 0:
            print('%.2f%% complete (down: %.1f kb/s up: %.1f kB/s p: %d) %s' %
                  (mt.progress * 100,
                   s.download_rate / 1000,
                   s.upload_rate / 1000,
                   s.num_peers,
                   mt.numbers()))
        now = time.time()
        current_state = (now, mt.progress)
        if current_state[-1] != last_state[-1]:
            last_state = current_state
        if last_state[0] < now - max_no_changes:
            sys.exit("Failed to fetch torrents in %ds" % max_no_changes)
        time.sleep(0.5)
    if mt.progress == 1:
        # ok
        # torrent lib dislikes forks there
        from subprocess import check_output
        args = sys.argv[:]
        args[-2] = 's'
        args.insert(0, sys.executable)
        print("Entering seeder mode")
        check_output(args, shell=False)
    else:
        # err
        sys.exit(1)


if __name__ == '__main__':
    mode = sys.argv[1]
    torrents = sys.argv[2]
    torrents = [x.split('|') for x in torrents.split(';')]
    print(repr(torrents))
    if mode == 'g':
        _getter(torrents, *sys.argv[3:])
    elif mode == 's':
        _seeder(torrents, *sys.argv[3:])
    else:
        sys.exit("`s` or `g` needed")
