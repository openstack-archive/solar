#!/usr/bin/python

import argparse
from ansible.playbook import PlayBook
from ansible import utils
from ansible import callbacks

def expose():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=str)
    args = parser.parse_args()

    stats = callbacks.AggregateStats()
    playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
    runner_cb = callbacks.PlaybookRunnerCallbacks(stats, verbose=utils.VERBOSITY)

    play = PlayBook(
        playbook=args.p,
        host_list=['localhost'],
        extra_vars={'var1': 'something', 'uuid': 'okay'},
        callbacks=playbook_cb,
        runner_callbacks=runner_cb,
        stats=stats,
        transport='local')
    return play.run()

expose()
