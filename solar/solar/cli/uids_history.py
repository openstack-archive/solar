import click
import os
import re

uids_history = os.path.join(os.getcwd(), '.solar_cli_uids')


def remember_uid(uid):
    """
    Remembers last 3 uids.
    Can be used then as `last`, `last1`, `last2` anywhere
    """
    try:
        with open(uids_history, 'rb') as f:
            hist = [x.strip() for x in f.readlines()]
    except IOError:
        hist = []
    hist.insert(0, uid)
    if len(hist) > 3:
        hist = hist[:3]
    with open(uids_history, 'wb') as f:
        f.write('\n'.join(hist))


def get_uid(given_uid):
    """
    Converts given uid to real uid.
    """
    matched = re.search('last(\d*)', given_uid)
    if matched:
        try:
            position = int(matched.group(1))
        except ValueError:
            position = 0
        with open(uids_history, 'rb') as f:
            uids = [x.strip() for x in f.readlines()]
        try:
            return uids[position]
        except IndexError:
            # fallback to original
            return given_uid
    return given_uid


class SolarUIDParameterType(click.types.StringParamType):
    """
    Type for solar changes uid.
    Works like a string but can convert `last(\d+)` to valid uid.
    """
    name = 'uid'

    def convert(self, value, param, ctx):
        value = click.types.StringParamType.convert(self, value, param, ctx)
        value = get_uid(value)
        return value


SOLARUID = SolarUIDParameterType()
