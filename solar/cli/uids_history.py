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

import os
import re

import click


UIDS_HISTORY = os.path.join(os.getcwd(), '.solar_cli_uids')


def remember_uid(uid):
    """
    Remembers last 3 uids.
    Can be used then as `last`, `last1`, `last2` anywhere
    """
    try:
        with open(UIDS_HISTORY, 'rb') as f:
            hist = [x.strip() for x in f.readlines()]
    except IOError:
        hist = []
    hist.insert(0, uid)
    if len(hist) > 3:
        hist = hist[:3]
    with open(UIDS_HISTORY, 'wb') as f:
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
        with open(UIDS_HISTORY, 'rb') as f:
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
        try:
            value = get_uid(value)
        except IOError:
            msg = ("Unable to locate file %r so"
                  "you can't use 'last' shortcuts" % UIDS_HISTORY)
            raise click.BadParameter(msg)
        return value


SOLARUID = SolarUIDParameterType()
